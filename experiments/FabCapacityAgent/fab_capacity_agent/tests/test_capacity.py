"""
FabCapacityAgent - 核心产能计算与 Agent 链路单元测试

覆盖范围:
  1) 数据库初始化与表结构
  2) MES 模拟数据完整性
  3) CapacityCalculator (OEE / WIP / Snapshot)
  4) Predictor (产能预测)
  5) BottleneckDetector (瓶颈检测)
  6) WhatIfSimulator (情景仿真)
  7) Agent 单 Agent 调用 (PerceptionAgent)
  8) Orchestrator 全链路 Pipeline

运行方式:
  # 方式 1: pytest (需先解决 pytest_flask 插件冲突)
  python -m pytest tests/test_capacity.py -v -p no:flask

  # 方式 2: 直接运行 (推荐, 无外部依赖)
  python tests/test_capacity.py

  # 方式 3: 运行单个测试
  python tests/test_capacity.py TestCapacityCalculator::test_oee_by_process
"""

import os
import sys
import time
from pathlib import Path

# 让脚本可直接运行: 把项目根加入 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import numpy as np

from utils.helpers import get_logger, safe_round, safe_div
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    TABLE_EQUIPMENT,
    TABLE_LOTS,
    TABLE_LOT_HISTORY,
    TABLE_EQUIPMENT_EVENTS,
    TABLE_DAILY_OUTPUT,
    TABLE_AGENT_LOGS,
    AGENT_PERCEPTION,
    STATUS_SUCCESS,
)
from models.database import get_db, DatabaseManager
from models.capacity import CapacitySnapshot, AgentLogDAO
from services.capacity_calculator import get_calculator, CapacityCalculator
from services.predictor import Predictor
from services.bottleneck_detector import BottleneckDetector
from services.what_if_simulator import WhatIfSimulator, ScenarioConfig

logger = get_logger("TestCapacity", level="INFO")


# =============================================================================
# 测试工具: 双模式运行器 (pytest / standalone)
# =============================================================================

def _run_as_standalone() -> None:
    """直接运行模式: 依次执行所有 test_* 方法,统计通过/失败。"""
    # 收集所有 Test* 类
    test_classes = []
    for name in dir(sys.modules[__name__]):
        obj = getattr(sys.modules[__name__], name)
        if isinstance(obj, type) and name.startswith("Test") and hasattr(obj, "__module__") and obj.__module__ == __name__:
            test_classes.append(obj)

    total = 0
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        setup = getattr(instance, "setup_method", None)
        if setup:
            try:
                setup()
            except Exception as exc:
                print(f"  [SETUP FAIL] {cls.__name__}: {exc}")
                continue

        methods = [m for m in dir(instance) if m.startswith("test_") and callable(getattr(instance, m))]
        for method_name in methods:
            total += 1
            method = getattr(instance, method_name)
            t0 = time.perf_counter()
            try:
                method()
                dur = (time.perf_counter() - t0) * 1000
                print(f"  ✓ {cls.__name__}::{method_name}  ({dur:.0f}ms)")
                passed += 1
            except Exception as exc:
                dur = (time.perf_counter() - t0) * 1000
                print(f"  ✗ {cls.__name__}::{method_name}  ({dur:.0f}ms)")
                print(f"      {type(exc).__name__}: {exc}")
                failed += 1
                errors.append((cls.__name__, method_name, exc))

    print()
    print("=" * 60)
    print(f"测试结果: {passed}/{total} 通过, {failed} 失败")
    if errors:
        print("\n失败详情:")
        for cls_name, m_name, exc in errors:
            print(f"  - {cls_name}::{m_name}: {type(exc).__name__}: {exc}")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


# =============================================================================
# 测试 1: 数据库初始化与表结构
# =============================================================================

class TestDatabase:
    """数据库初始化与表结构测试。"""

    def setup_method(self) -> None:
        self.db = get_db()

    def test_connection(self) -> None:
        """测试数据库连接是否正常。"""
        conn = self.db.get_connection()
        assert conn is not None, "数据库连接失败"

    def test_tables_exist(self) -> None:
        """测试所有业务表是否已创建。"""
        required_tables = [
            TABLE_EQUIPMENT, TABLE_LOTS, TABLE_LOT_HISTORY,
            TABLE_EQUIPMENT_EVENTS, TABLE_DAILY_OUTPUT, TABLE_AGENT_LOGS,
        ]
        rows = self.db.query("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {r["name"] for r in rows}
        for tbl in required_tables:
            assert tbl in existing, f"表 {tbl} 不存在"

    def test_equipment_count(self) -> None:
        """测试设备表行数 (预期 120 台)。"""
        cnt = self.db.count(TABLE_EQUIPMENT)
        assert cnt == 120, f"设备数应为 120, 实际 {cnt}"

    def test_lot_history_not_empty(self) -> None:
        """测试工序历史表非空。"""
        cnt = self.db.count(TABLE_LOT_HISTORY)
        assert cnt > 0, "lot_history 表为空, 请先运行数据生成器"

    def test_daily_output_rows(self) -> None:
        """测试日产出汇总表有数据。"""
        cnt = self.db.count(TABLE_DAILY_OUTPUT)
        assert cnt > 0, "daily_output 表为空"


# =============================================================================
# 测试 2: CapacityCalculator 核心计算
# =============================================================================

class TestCapacityCalculator:
    """产能计算器核心方法测试。"""

    def setup_method(self) -> None:
        self.calc = get_calculator()

    def test_oee_by_process(self) -> None:
        """测试按工序计算 OEE, 返回 DataFrame 含必要列。"""
        import datetime as dt
        now_t = dt.datetime.now()
        start_t = now_t - dt.timedelta(hours=24)
        df = self.calc.oee_by_process(start_t, now_t)

        assert df is not None, "oee_by_process 返回 None"
        # 列存在性
        for col in ["process", "oee"]:
            assert col in df.columns, f"缺少列: {col}"
        # OEE 在 0~1 之间
        if not df.empty:
            oee_vals = df["oee"].dropna()
            assert (oee_vals >= 0).all() and (oee_vals <= 1).all(), "OEE 值超出 [0,1] 范围"

    def test_wip_distribution(self) -> None:
        """测试 WIP 分布查询。"""
        df = self.calc.wip_distribution()
        assert df is not None, "wip_distribution 返回 None"
        assert "process" in df.columns, "缺少 process 列"
        assert "wafers" in df.columns, "缺少 wafers 列"
        # 应包含全部 8 道工序
        assert len(df) >= len(ALL_PROCESSES), f"WIP 分布行数 {len(df)} < 工序数 {len(ALL_PROCESSES)}"

    def test_build_snapshot(self) -> None:
        """测试构建全厂产能快照。"""
        snap = self.calc.build_snapshot(window_hours=24)
        assert isinstance(snap, CapacitySnapshot), "build_snapshot 应返回 CapacitySnapshot"

        # 全厂 OEE 在合理范围
        assert 0 <= snap.overall_oee <= 1, f"overall_oee={snap.overall_oee} 超出 [0,1]"
        # WIP 非负
        assert snap.wip_total_wafers >= 0, f"wip_total_wafers={snap.wip_total_wafers} 为负"
        # by_process 非空
        assert len(snap.by_process) > 0, "by_process 为空"
        # 快照可序列化
        d = snap.to_dict()
        assert "overall_oee" in d, "to_dict 缺少 overall_oee"
        assert "by_process" in d, "to_dict 缺少 by_process"

    def test_snapshot_to_json(self) -> None:
        """测试快照 JSON 序列化。"""
        import json
        snap = self.calc.build_snapshot(window_hours=24)
        js = snap.to_json()
        parsed = json.loads(js)
        assert "overall_oee" in parsed, "JSON 缺少 overall_oee"

    def test_theoretical_capacity(self) -> None:
        """测试理论产能计算 (按工序)。"""
        df = self.calc.theoretical_capacity_by_process()
        assert df is not None, "theoretical_capacity_by_process 返回 None"
        assert not df.empty, "理论产能为空"


# =============================================================================
# 测试 3: Predictor 产能预测
# =============================================================================

class TestPredictor:
    """产能预测服务测试。"""

    def setup_method(self) -> None:
        self.pred = Predictor()

    def test_forecast_output(self) -> None:
        """测试日产出预测 (本地模式, 不用 LLM)。"""
        fr = self.pred.forecast_output(
            horizon_days=7,
            history_days=30,
            target="output_wafers",
            product_type="ALL",
            use_llm=False,
        )
        assert fr is not None, "forecast_output 返回 None"
        # 预测长度 == horizon
        assert len(fr.predicted) == 7, f"预测长度 {len(fr.predicted)} != 7"
        # 置信区间长度一致
        assert len(fr.lower_ci) == 7, "lower_ci 长度不对"
        assert len(fr.upper_ci) == 7, "upper_ci 长度不对"
        # 下界 <= 预测 <= 上界
        for p, lo, hi in zip(fr.predicted, fr.lower_ci, fr.upper_ci):
            assert lo <= p <= hi, f"CI 范围异常: lo={lo}, pred={p}, hi={hi}"

    def test_forecast_multi(self) -> None:
        """测试多目标预测。"""
        results = self.pred.forecast_multi(
            targets=["output_wafers", "move_count"],
            horizon_days=7,
            history_days=30,
        )
        assert "output_wafers" in results, "缺少 output_wafers 预测"
        assert "move_count" in results, "缺少 move_count 预测"


# =============================================================================
# 测试 4: BottleneckDetector 瓶颈检测
# =============================================================================

class TestBottleneckDetector:
    """瓶颈检测服务测试。"""

    def setup_method(self) -> None:
        self.bd = BottleneckDetector()

    def test_detect_and_report(self) -> None:
        """测试瓶颈检测报告生成。"""
        report = self.bd.detect_and_report(window_hours=24)
        assert report is not None, "detect_and_report 返回 None"
        # bottlenecks 是列表
        assert isinstance(report.bottlenecks, list), "bottlenecks 应为列表"
        # causes 是列表
        assert isinstance(report.causes, list), "causes 应为列表"
        # suggestions 是列表
        assert isinstance(report.suggestions, list), "suggestions 应为列表"
        # utilization_breakdown 是 DataFrame
        assert isinstance(report.utilization_breakdown, pd.DataFrame), "utilization_breakdown 应为 DataFrame"
        # 至少识别出一些瓶颈 (可能为空, 但不应报错)
        if report.bottlenecks:
            b0 = report.bottlenecks[0]
            assert "process" in b0, "瓶颈项缺少 process 字段"


# =============================================================================
# 测试 5: WhatIfSimulator 情景仿真
# =============================================================================

class TestWhatIfSimulator:
    """What-If 仿真器测试。"""

    def setup_method(self) -> None:
        self.ws = WhatIfSimulator()

    def test_run_baseline(self) -> None:
        """测试 Baseline 情景运行。"""
        result = self.ws.run_baseline()
        assert result is not None, "run_baseline 返回 None"
        assert result.name == "Baseline", f"Baseline 名称不对: {result.name}"
        assert result.total_effective_wafers_per_week > 0, "Baseline 周产能应 > 0"
        assert 0 <= result.overall_oee <= 1, f"Baseline OEE={result.overall_oee} 超范围"

    def test_preset_scenarios(self) -> None:
        """测试预设情景列表。"""
        scenarios = self.ws.preset_scenarios()
        assert isinstance(scenarios, list), "preset_scenarios 应返回列表"
        assert len(scenarios) > 0, "预设情景为空"
        # 每个都是 ScenarioConfig
        for sc in scenarios:
            assert isinstance(sc, ScenarioConfig), f"情景类型错误: {type(sc)}"
            assert hasattr(sc, "name"), "ScenarioConfig 缺少 name"

    def test_compare_scenarios(self) -> None:
        """测试多情景对比。"""
        scenarios = self.ws.preset_scenarios()
        df = self.ws.compare_scenarios(scenarios)
        assert df is not None, "compare_scenarios 返回 None"
        assert not df.empty, "对比结果为空"
        # 应有 name 列
        assert "name" in df.columns, "对比结果缺少 name 列"
        # 应包含 Baseline
        assert "Baseline" in df["name"].values, "对比结果缺少 Baseline"

    def test_custom_scenario(self) -> None:
        """测试自定义情景 (加设备)。"""
        cfg = ScenarioConfig(
            name="TestAddEquip",
            description="测试加 1 台 DIFF 设备",
            add_equipment={"DIFF": 1},
            oee_delta=0.0,
            new_product_demand_ratio=0.0,
            new_product_name=None,
            pm_changes={},
        )
        result = self.ws.run_scenario(cfg)
        assert result is not None, "run_scenario 返回 None"
        assert result.name == "TestAddEquip", f"情景名称不对: {result.name}"
        # 加设备后周产能应 >= Baseline
        baseline = self.ws.run_baseline()
        assert result.total_effective_wafers_per_week >= baseline.total_effective_wafers_per_week, \
            "加设备后产能应 >= Baseline"


# =============================================================================
# 测试 6: Agent 单 Agent 调用
# =============================================================================

class TestAgents:
    """Agent 框架测试 (单 Agent + 全链路)。"""

    def test_perception_agent(self) -> None:
        """测试 PerceptionAgent 单独运行。"""
        from agents.perception_agent import PerceptionAgent
        from agents.base_agent import AgentContext

        agent = PerceptionAgent(llm=None)  # 关闭 LLM 加速
        ctx = AgentContext(run_id="test_perception", trigger="test")
        ctx.extra["window_hours"] = 24
        ctx.extra["history_days"] = 7

        result = agent.run(ctx)
        assert result is not None, "PerceptionAgent.run 返回 None"
        assert result.get("status") == STATUS_SUCCESS, f"PerceptionAgent 状态: {result.get('status')}"
        # output 应包含 snapshot
        output = result.get("output", {})
        assert output is not None, "output 为空"

    def test_orchestrator_single(self) -> None:
        """测试 Orchestrator 单 Agent 调用。"""
        from agents.orchestrator import get_orchestrator

        orch = get_orchestrator()
        # 关闭 LLM
        for a in orch.agents.values():
            a.llm = None

        result = orch.run_single(AGENT_PERCEPTION, window_hours=24, history_days=7)
        assert result is not None, "run_single 返回 None"
        assert result.get("status") == STATUS_SUCCESS, f"单 Agent 状态: {result.get('status')}"


# =============================================================================
# 测试 7: Orchestrator 全链路 (耗时较长, 可选)
# =============================================================================

class TestOrchestratorPipeline:
    """Orchestrator 全链路测试 (耗时约 15~30s)。"""

    def test_full_pipeline(self) -> None:
        """测试全链路 Pipeline (Perception → Analysis → Decision → Execution)。"""
        from agents.orchestrator import get_orchestrator

        orch = get_orchestrator()
        # 关闭 LLM 加速测试
        for a in orch.agents.values():
            a.llm = None

        result = orch.run_full_pipeline(
            user_query="测试全链路",
            trigger="unit_test",
            window_hours=24,
            history_days=7,
        )
        assert result is not None, "run_full_pipeline 返回 None"
        # 状态应为 success 或 partial (允许部分成功)
        assert result.status in ("success", "partial"), f"Pipeline 状态异常: {result.status}"
        # 至少 Perception 应成功
        steps = result.pipeline_steps
        assert len(steps) > 0, "pipeline_steps 为空"
        assert steps[0].status == STATUS_SUCCESS, "Perception 步骤应成功"
        # 应有最终报告
        assert result.final_report != "", "最终报告为空"


# =============================================================================
# 测试 8: 工具函数
# =============================================================================

class TestUtils:
    """工具函数测试。"""

    def test_safe_div(self) -> None:
        """测试安全除法。"""
        assert safe_div(10, 2) == 5.0
        assert safe_div(1, 0) == 0.0
        assert safe_div(1, 0, default=-1.0) == -1.0
        assert safe_div("a", "b") == 0.0

    def test_safe_round(self) -> None:
        """测试安全四舍五入。"""
        from utils.helpers import safe_round
        assert safe_round(3.14159, 2) == 3.14
        assert safe_round(3.145, 2) == 3.15  # ROUND_HALF_UP
        assert safe_round(None) == 0.0
        assert safe_round(float("nan")) == 0.0

    def test_constants(self) -> None:
        """测试常量定义。"""
        assert len(ALL_PROCESSES) == 8, f"工序数应为 8, 实际 {len(ALL_PROCESSES)}"
        assert "PHOTO" in PROCESS_NAME_CN, "缺少 PHOTO 工序"
        assert PROCESS_NAME_CN["PHOTO"] == "光刻", "PHOTO 中文名不对"


# =============================================================================
# 入口: 支持 pytest 和直接运行
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FabCapacityAgent - 单元测试 (standalone 模式)")
    print("=" * 60)
    print()
    _run_as_standalone()
else:
    # pytest 模式: 不做额外操作, 让 pytest 自动发现 test_* 方法
    pass

"""
FabCapacityAgent - What-If 情景模拟器 (WhatIfSimulator)

支持四类产能优化情景的模拟与对比:
  1) AddEquipment   - 增加设备 (capacity expansion)
  2) AdjustOEE      - 调整 OEE 三要素 (improvement program)
  3) NewProduct     - 导入新产品 (capacity reservation)
  4) ModifyPM       - 修改 PM 计划 (PM window / frequency)

每个情景计算:
  - Before vs After 的 全厂/工序级 KPI 对比
  - 产能增量 (片/周, %)
  - 投入产出比 (ROI proxy)
  - 风险等级 (蒙特卡洛抽样估算产出分布 P5/P50/P95)

设计原则:
  - 不修改真实 DB, 全部在内存 DataFrame 上模拟
  - 情景可叠加 (Scenario Compose), 形成组合优化方案
  - 调用 CapacityCalculator.theoretical_capacity_by_process() 作为基准
"""

import datetime as dt
import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from copy import deepcopy

import numpy as np
import pandas as pd

from services.capacity_calculator import CapacityCalculator, get_calculator
from utils.helpers import (
    get_logger,
    try_except,
    safe_div,
    safe_round,
    get_config,
)
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    PROCESS_EQUIPMENT_TYPE,
    ALL_PRODUCTS,
    PRODUCT_NAME_CN,
)

logger = get_logger("WhatIfSimulator", level="INFO")


# =============================================================================
# 数据类
# =============================================================================

@dataclass
class ScenarioConfig:
    """单个 What-If 情景配置。"""
    name: str = "Baseline"                                  # 情景名
    description: str = ""                                   # 中文描述

    # (1) 增加设备: {process: add_count}
    add_equipment: Dict[str, int] = field(default_factory=dict)

    # (2) 调整 OEE 三要素 (绝对增量): {process: {"availability": +0.02, "performance": +0.01, "quality": 0}}
    oee_delta: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # (3) 导入新产品: 占用每周总产能的比例 (0~1)
    new_product_demand_ratio: float = 0.0
    new_product_name: str = "New_Product"

    # (4) 修改 PM 计划: {process: {"pm_frequency_h": 240, "pm_duration_h": 6}}
    pm_changes: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioResult:
    """单个情景模拟结果。"""
    name: str = "Baseline"
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

    # 模拟后的 工序级 DataFrame (与 theoretic 表对齐 + 实际值)
    process_summary: pd.DataFrame = field(default_factory=pd.DataFrame)

    # 全厂汇总
    total_effective_wafers_per_week: float = 0.0
    total_theoretic_wafers_per_week: float = 0.0
    overall_oee: float = 0.0

    # 增量对比 (vs baseline)
    delta_wafers_per_week: float = 0.0
    delta_pct: float = 0.0
    delta_oee: float = 0.0

    # 蒙特卡洛风险评估
    mc_p5: float = 0.0       # 悲观产出
    mc_p50: float = 0.0      # 中位产出
    mc_p95: float = 0.0      # 乐观产出
    mc_std: float = 0.0
    risk_level: str = "L"    # L(低)/M(中)/H(高)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "total_effective_wafers_per_week": self.total_effective_wafers_per_week,
            "total_theoretic_wafers_per_week": self.total_theoretic_wafers_per_week,
            "overall_oee": self.overall_oee,
            "delta_wafers_per_week": self.delta_wafers_per_week,
            "delta_pct": self.delta_pct,
            "delta_oee": self.delta_oee,
            "mc_p5": self.mc_p5,
            "mc_p50": self.mc_p50,
            "mc_p95": self.mc_p95,
            "mc_std": self.mc_std,
            "risk_level": self.risk_level,
            "process_summary": self.process_summary.to_dict(orient="records"),
        }


# =============================================================================
# 主类: WhatIfSimulator
# =============================================================================

class WhatIfSimulator:
    """
    What-If 情景模拟器。

    用法:
        sim = WhatIfSimulator()
        baseline = sim.run_baseline()

        # 情景1: 给 DIFF 工序加 2 台设备
        sc = ScenarioConfig(name="AddDiff2", add_equipment={"DIFF": 2})
        result = sim.run_scenario(sc)

        # 对比
        print(result.delta_wafers_per_week, result.delta_pct)
    """

    def __init__(self, calc: Optional[CapacityCalculator] = None) -> None:
        self.calc = calc or get_calculator()

        # 基础参数
        self.hours_per_week: int = int(get_config("production", "operating_hours", default=168))
        self.wafers_per_lot: int = int(get_config("production", "wafers_per_lot", default=25))
        self.equip_dist: Dict[str, int] = (
            get_config("equipment", "distribution", default={}) or {}
        )

        # OEE 基准 (来自 settings)
        oee_bench = get_config("data_generator", "oee_benchmark", default={}) or {}
        self.bench_a = float(oee_bench.get("availability", 0.9))
        self.bench_p = float(oee_bench.get("performance", 0.85))
        self.bench_q = float(oee_bench.get("quality", 0.95))
        self.bench_oee = self.bench_a * self.bench_p * self.bench_q

        # 工序标准时间
        self.std_times: Dict[str, float] = {
            p: float(get_config("production", "processes", default={})
                     .get(p, {}).get("process_time", 2.0))
            for p in ALL_PROCESSES
        }

        # 故障参数 (蒙特卡洛用)
        fp = get_config("data_generator", "failure_params", default={}) or {}
        self.mtbf = float(fp.get("mtbf", 48))
        self.mttr = float(fp.get("mttr", 4))
        self.pm_freq = float(fp.get("pm_frequency", 168))
        self.pm_dur = float(fp.get("pm_duration", 8))

        # 蒙特卡洛配置
        self.mc_iterations: int = int(
            get_config("simulator", "monte_carlo_iterations", default=100)
        )

        # 缓存 baseline
        self._baseline: Optional[ScenarioResult] = None

    # =========================================================================
    # Baseline
    # =========================================================================

    @try_except(default_return=ScenarioResult(name="Baseline"))
    def run_baseline(self) -> ScenarioResult:
        """计算基线 (当前真实状态) 的 ScenarioResult, 作为对照。"""
        df = self.calc.theoretical_capacity_by_process()
        if df.empty:
            logger.warning("基线 theoretic 表为空")
            return ScenarioResult(name="Baseline")

        # 全厂汇总
        total_eff = float(df["effective_wafers_per_week"].sum())
        total_th = float(df["theoretic_wafers_per_week"].sum())
        oee = safe_div(total_eff, total_th, default=0.0)

        result = ScenarioResult(
            name="Baseline",
            description="当前真实状态基线",
            config={},
            process_summary=df.copy(),
            total_effective_wafers_per_week=total_eff,
            total_theoretic_wafers_per_week=total_th,
            overall_oee=oee,
        )
        # 蒙特卡洛风险评估
        mc_p5, mc_p50, mc_p95, mc_std = self._monte_carlo(df)
        result.mc_p5, result.mc_p50, result.mc_p95, result.mc_std = (
            mc_p5, mc_p50, mc_p95, mc_std
        )
        result.risk_level = self._risk_level(mc_std, mc_p50)
        self._baseline = result
        logger.info(f"Baseline: 全厂有效产能={total_eff:,.0f}片/周, OEE={oee*100:.2f}%, "
                    f"P5/P50/P95={mc_p5:,.0f}/{mc_p50:,.0f}/{mc_p95:,.0f}, 风险={result.risk_level}")
        return result

    # =========================================================================
    # 单情景模拟
    # =========================================================================

    @try_except(default_return=ScenarioResult(name="Error"))
    def run_scenario(self, scenario: ScenarioConfig) -> ScenarioResult:
        """
        执行一个 What-If 情景, 返回与 baseline 的对比结果。
        """
        # 确保 baseline 已计算
        if self._baseline is None:
            self.run_baseline()
        baseline = self._baseline
        if baseline is None or baseline.process_summary.empty:
            return ScenarioResult(name=scenario.name)

        # 基于 baseline 的 theoretic 表做叠加修改 (深拷贝避免污染)
        df = baseline.process_summary.copy()

        # ---- (1) 增加设备 ----
        for proc, n_add in scenario.add_equipment.items():
            if proc not in df["process"].values:
                continue
            mask = df["process"] == proc
            old_n = int(df.loc[mask, "equipment_count"].iloc[0])
            new_n = old_n + int(n_add)
            df.loc[mask, "equipment_count"] = new_n
            # 理论产能 + 有效产能 都按设备数线性增长 (OEE 不变)
            ratio = safe_div(new_n, old_n, default=1.0)
            df.loc[mask, "theoretic_wafers_per_week"] = (
                df.loc[mask, "theoretic_wafers_per_week"] * ratio
            )
            df.loc[mask, "effective_wafers_per_week"] = (
                df.loc[mask, "effective_wafers_per_week"] * ratio
            )
            df.loc[mask, "theoretic_uph"] = df.loc[mask, "theoretic_uph"] * ratio
            df.loc[mask, "effective_uph"] = df.loc[mask, "effective_uph"] * ratio

        # ---- (2) 调整 OEE ----
        # oee_delta 支持两种形式:
        #   (a) Dict[process, {availability/performance/quality: delta}]  按工序精细调整
        #   (b) float  统一调整 (把 delta 平均分配到 A/P/Q 三个要素)
        oee_delta = scenario.oee_delta
        if isinstance(oee_delta, (int, float)):
            # 统一调整: 转换为所有工序的 dict
            uniform_delta = float(oee_delta) / 3.0  # 平均分到 A/P/Q
            oee_delta = {p: {"availability": uniform_delta,
                             "performance": uniform_delta,
                             "quality": uniform_delta}
                         for p in df["process"].unique().tolist()}

        for proc, delta in (oee_delta or {}).items():
            if proc not in df["process"].values:
                continue
            mask = df["process"] == proc
            old_oee = float(df.loc[mask, "benchmark_oee"].iloc[0])
            # delta 可以是 dict 或数值
            if isinstance(delta, dict):
                da = float(delta.get("availability", 0))
                dp = float(delta.get("performance", 0))
                dq = float(delta.get("quality", 0))
            else:
                # 数值: 平均分到 A/P/Q
                da = dp = dq = float(delta) / 3.0
            # 重新构造 OEE 三要素 (基于基准, 不能超 1.0)
            new_a = min(1.0, max(0.0, self.bench_a + da))
            new_p = min(1.0, max(0.0, self.bench_p + dp))
            new_q = min(1.0, max(0.0, self.bench_q + dq))
            new_oee = new_a * new_p * new_q
            df.loc[mask, "benchmark_oee"] = new_oee
            # 有效产能 = 理论 × 新 OEE
            df.loc[mask, "effective_wafers_per_week"] = (
                df.loc[mask, "theoretic_wafers_per_week"] * new_oee
            )
            df.loc[mask, "effective_uph"] = (
                df.loc[mask, "theoretic_uph"] * new_oee
            )

        # ---- (3) 修改 PM 计划 ----
        # PM 变化影响 Availability: 新A = 1 - pm_dur/pm_freq (近似)
        for proc, pm in scenario.pm_changes.items():
            if proc not in df["process"].values:
                continue
            mask = df["process"] == proc
            new_pm_freq = float(pm.get("pm_frequency_h", self.pm_freq))
            new_pm_dur = float(pm.get("pm_duration_h", self.pm_dur))
            # 旧 PM 占比
            old_pm_ratio = self.pm_dur / self.pm_freq
            new_pm_ratio = new_pm_dur / new_pm_freq
            # Availability 变化: 增加 (old_pm_ratio - new_pm_ratio)
            delta_a = old_pm_ratio - new_pm_ratio
            old_oee = float(df.loc[mask, "benchmark_oee"].iloc[0])
            # 估算旧 A (基准), 重算新 A
            old_a = self.bench_a
            new_a = min(1.0, max(0.0, old_a + delta_a))
            new_oee = new_a * self.bench_p * self.bench_q
            df.loc[mask, "benchmark_oee"] = new_oee
            df.loc[mask, "effective_wafers_per_week"] = (
                df.loc[mask, "theoretic_wafers_per_week"] * new_oee
            )
            df.loc[mask, "effective_uph"] = (
                df.loc[mask, "theoretic_uph"] * new_oee
            )

        # ---- (4) 新产品占用 ----
        # 简化: 总有效产能 × (1 - new_product_demand_ratio) 为现有产品可用
        if scenario.new_product_demand_ratio > 0:
            df["effective_wafers_per_week"] = df["effective_wafers_per_week"] * (
                1.0 - scenario.new_product_demand_ratio
            )
            df["effective_uph"] = df["effective_uph"] * (
                1.0 - scenario.new_product_demand_ratio
            )

        # 全厂汇总
        total_eff = float(df["effective_wafers_per_week"].sum())
        total_th = float(df["theoretic_wafers_per_week"].sum())
        oee = safe_div(total_eff, total_th, default=0.0)

        # 增量
        delta_w = total_eff - baseline.total_effective_wafers_per_week
        delta_pct = safe_div(delta_w, baseline.total_effective_wafers_per_week, default=0.0)
        delta_oee = oee - baseline.overall_oee

        # 蒙特卡洛
        mc_p5, mc_p50, mc_p95, mc_std = self._monte_carlo(df)
        risk = self._risk_level(mc_std, mc_p50)

        result = ScenarioResult(
            name=scenario.name,
            description=scenario.description or scenario.name,
            config=scenario.to_dict(),
            process_summary=df,
            total_effective_wafers_per_week=safe_round(total_eff, 0),
            total_theoretic_wafers_per_week=safe_round(total_th, 0),
            overall_oee=safe_round(oee, 4),
            delta_wafers_per_week=safe_round(delta_w, 0),
            delta_pct=safe_round(delta_pct, 4),
            delta_oee=safe_round(delta_oee, 4),
            mc_p5=safe_round(mc_p5, 0),
            mc_p50=safe_round(mc_p50, 0),
            mc_p95=safe_round(mc_p95, 0),
            mc_std=safe_round(mc_std, 0),
            risk_level=risk,
        )
        logger.info(f"情景 [{scenario.name}]: 有效产能={total_eff:,.0f}片/周 "
                    f"(Δ={delta_w:+,.0f}, {delta_pct*100:+.2f}%), OEE={oee*100:.2f}%, "
                    f"P5/P50/P95={mc_p5:,.0f}/{mc_p50:,.0f}/{mc_p95:,.0f}, 风险={risk}")
        return result

    # =========================================================================
    # 多情景对比
    # =========================================================================

    @try_except(default_return=pd.DataFrame())
    def compare_scenarios(self, scenarios: List[ScenarioConfig]) -> pd.DataFrame:
        """
        批量执行多个情景, 返回对比 DataFrame (便于 Plotly 渲染)。
        """
        if self._baseline is None:
            self.run_baseline()

        rows = []
        # 加上 baseline
        if self._baseline is not None:
            b = self._baseline
            rows.append({
                "name": "Baseline",
                "description": "当前真实状态",
                "total_wafers_per_week": b.total_effective_wafers_per_week,
                "delta_wafers": 0.0,
                "delta_pct": 0.0,
                "overall_oee": b.overall_oee,
                "mc_p5": b.mc_p5,
                "mc_p50": b.mc_p50,
                "mc_p95": b.mc_p95,
                "risk_level": b.risk_level,
            })

        for sc in scenarios:
            r = self.run_scenario(sc)
            rows.append({
                "name": r.name,
                "description": r.description,
                "total_wafers_per_week": r.total_effective_wafers_per_week,
                "delta_wafers": r.delta_wafers_per_week,
                "delta_pct": r.delta_pct,
                "overall_oee": r.overall_oee,
                "mc_p5": r.mc_p5,
                "mc_p50": r.mc_p50,
                "mc_p95": r.mc_p95,
                "risk_level": r.risk_level,
            })

        return pd.DataFrame(rows)

    # =========================================================================
    # 预设情景 (供 UI 快速调用)
    # =========================================================================

    @try_except(default_return=[])
    def preset_scenarios(self) -> List[ScenarioConfig]:
        """返回一组预设 What-If 情景, 覆盖常见优化方向。"""
        presets = [
            ScenarioConfig(
                name="Add_DIFF_2",
                description="给瓶颈工序扩散(DIFF)增加 2 台设备",
                add_equipment={"DIFF": 2},
            ),
            ScenarioConfig(
                name="Add_IMP_3",
                description="给离子注入(IMP)增加 3 台设备 (缓解WIP积压)",
                add_equipment={"IMP": 3},
            ),
            ScenarioConfig(
                name="OEE_+5pct_All",
                description="全厂OEE提升5% (假设通过预测性维护+SMED)",
                oee_delta={p: {"availability": 0.03, "performance": 0.015, "quality": 0.005}
                            for p in ALL_PROCESSES},
            ),
            ScenarioConfig(
                name="OEE_DIFF_+10pct",
                description="扩散工序OEE提升10% (专项改善)",
                oee_delta={"DIFF": {"availability": 0.05, "performance": 0.04, "quality": 0.01}},
            ),
            ScenarioConfig(
                name="PM_Optimize",
                description="全厂PM周期延长至240h, 时长压缩至6h",
                pm_changes={p: {"pm_frequency_h": 240, "pm_duration_h": 6}
                              for p in ALL_PROCESSES},
            ),
            ScenarioConfig(
                name="NewProduct_10pct",
                description="导入新产品, 占用10%总产能",
                new_product_demand_ratio=0.10,
                new_product_name="Memory_D_New",
            ),
            ScenarioConfig(
                name="Combo_DIFF",
                description="组合方案: DIFF增1台+OEE+5%+PM优化",
                add_equipment={"DIFF": 1},
                oee_delta={"DIFF": {"availability": 0.03, "performance": 0.015, "quality": 0.005}},
                pm_changes={"DIFF": {"pm_frequency_h": 240, "pm_duration_h": 6}},
            ),
        ]
        return presets

    # =========================================================================
    # 内部: 蒙特卡洛 + 风险分级
    # =========================================================================

    def _monte_carlo(self, df: pd.DataFrame) -> Tuple[float, float, float, float]:
        """
        蒙特卡洛抽样: 对每工序的 effective_wafers_per_week 加噪声,
        模拟设备故障/性能波动的随机性, 返回 P5/P50/P95/std。
        """
        if df.empty or "effective_wafers_per_week" not in df.columns:
            return 0.0, 0.0, 0.0, 0.0

        base = df["effective_wafers_per_week"].astype(float).values
        n_iter = max(20, self.mc_iterations)
        rng = np.random.default_rng(seed=42)

        # 每工序的波动幅度 (CV = std/mean)
        # 利用率越高的工序波动越大 (越接近瓶颈)
        cv = 0.05  # 默认5%
        if "utilization" in df.columns:
            util = df["utilization"].astype(float).fillna(0).values
            cv_arr = 0.03 + 0.10 * util  # 3%~13%
        else:
            cv_arr = np.full(len(base), cv)

        samples = np.zeros(n_iter)
        for i in range(n_iter):
            # 每工序独立抽样: 正态分布乘子
            multipliers = rng.normal(1.0, cv_arr)
            multipliers = np.clip(multipliers, 0.5, 1.5)  # 限制极端值
            samples[i] = float(np.sum(base * multipliers))

        p5 = float(np.percentile(samples, 5))
        p50 = float(np.percentile(samples, 50))
        p95 = float(np.percentile(samples, 95))
        std = float(np.std(samples))
        return p5, p50, p95, std

    def _risk_level(self, std: float, p50: float) -> str:
        """根据变异系数 CV = std/p50 划分风险等级。"""
        cv = safe_div(std, max(1.0, p50), default=0.0)
        if cv < 0.05:
            return "L"  # 低风险
        if cv < 0.10:
            return "M"  # 中风险
        return "H"      # 高风险


# =============================================================================
# 单例
# =============================================================================

_simulator_instance: Optional[WhatIfSimulator] = None


def get_simulator() -> WhatIfSimulator:
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = WhatIfSimulator()
    return _simulator_instance


# =============================================================================
# 自检
# =============================================================================

if __name__ == "__main__":
    sim = get_simulator()

    print("=== Baseline ===")
    b = sim.run_baseline()
    print(f"  有效产能: {b.total_effective_wafers_per_week:,.0f} 片/周")
    print(f"  OEE: {b.overall_oee*100:.2f}%")
    print(f"  蒙特卡洛 P5/P50/P95: {b.mc_p5:,.0f} / {b.mc_p50:,.0f} / {b.mc_p95:,.0f}")
    print(f"  风险等级: {b.risk_level}")

    print("\n=== 预设情景对比 ===")
    presets = sim.preset_scenarios()
    df = sim.compare_scenarios(presets)
    display_cols = ["name", "total_wafers_per_week", "delta_wafers",
                    "delta_pct", "overall_oee", "mc_p50", "risk_level"]
    print(df[display_cols].to_string(index=False))

    print("\n=== 单情景明细 (Combo_DIFF) ===")
    combo_result = sim.run_scenario(presets[-1])
    print(combo_result.process_summary[
        ["process", "equipment_count", "theoretic_wafers_per_week",
         "effective_wafers_per_week", "benchmark_oee"]
    ].to_string(index=False))

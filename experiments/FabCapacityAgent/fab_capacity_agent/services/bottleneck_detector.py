"""
FabCapacityAgent - 瓶颈检测与根因分析服务 (BottleneckDetector)

职责:
  1) TOC 约束理论检测 - 长期产能约束 (System Constraint)
  2) 瞬时瓶颈检测     - 近24h/48h 阻塞热点 (Transient Bottleneck)
  3) 根因分解          - 把利用率拆成 (Down / PM / Setup / Idle) 四象限
  4) 量化改进收益      - 每项建议预估改善后 OEE / 有效产能增量
  5) LLM 增强建议      - 若 LLM 可用, 给出更贴合 Fab 场景的行动项

瓶颈判定 (组合规则, 非单一阈值):
  (a) Utilization > 85%  高负载
  (b) WIP Queue > 平均WIP的1.5倍  在制品积压
  (c) 累计 Down/PM 时长 > 工序Top3  计划/非计划停机突出
  (d) 该工序 Move Throughput / 理论 < 60%  产出不足

任何工序满足 (a) + (b 或 c 或 d) => 判为瓶颈, 严重度加权排序。
"""

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd

from models.database import get_db, DatabaseManager
from services.capacity_calculator import CapacityCalculator, get_calculator
from utils.helpers import (
    get_logger,
    try_except,
    safe_div,
    safe_round,
    parse_datetime,
    get_config,
)
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    EVENT_EQUIP_DOWN,
    EVENT_PM_START,
    EVENT_SETUP_START,
)
from utils.llm_client import LLMClient, get_llm, PROVIDER_DEEPSEEK

logger = get_logger("BottleneckDetector", level="INFO")


# =============================================================================
# 数据类
# =============================================================================

@dataclass
class BottleneckCause:
    """单一瓶颈根因。"""
    process: str
    dimension: str               # DownTime / PM / Setup / Performance / Capacity / Other
    severity_score: float        # 0~1
    quantitative_indicator: str  # 可量化描述, 如 "扩散工序平均故障间隔=21h(目标48h)"
    detail: str                  # 中文说明


@dataclass
class BottleneckSuggestion:
    """改进建议项。"""
    process: str
    category: str                # 设备 / 工艺 / 计划 / 维护 / 其他
    action: str                  # 具体行动
    expected_improvement: Dict[str, float] = field(default_factory=dict)  # oee增加量, 产能增量
    priority: int = 1            # 1高 / 2中 / 3低
    effort: str = "M"            # S/M/L 实施成本


@dataclass
class BottleneckReport:
    """结构化瓶颈报告。"""
    snapshot_time: dt.datetime = field(default_factory=lambda: dt.datetime.now())
    window_hours: int = 24

    # 瓶颈工序列表 (按严重度降序)
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    # 每工序根因列表
    causes: List[BottleneckCause] = field(default_factory=list)
    # 改进建议列表
    suggestions: List[BottleneckSuggestion] = field(default_factory=list)

    # 辅助: 全工序利用率四象限拆解 (Run/Down/PM/Setup/Idle 各自占比)
    utilization_breakdown: pd.DataFrame = field(default_factory=pd.DataFrame)

    # LLM 是否增强了建议
    llm_enhanced: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_time": self.snapshot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "window_hours": self.window_hours,
            "bottlenecks": self.bottlenecks,
            "causes": [asdict(c) for c in self.causes],
            "suggestions": [asdict(s) for s in self.suggestions],
            "llm_enhanced": self.llm_enhanced,
        }


# =============================================================================
# 主类
# =============================================================================

class BottleneckDetector:
    """瓶颈检测器 + 根因分析 + 改进建议。"""

    def __init__(
        self,
        calc: Optional[CapacityCalculator] = None,
        db: Optional[DatabaseManager] = None,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.calc = calc or get_calculator()
        self.db = db or get_db()

        # 阈值
        self.util_threshold: float = float(
            get_config("agent", "analysis_agent", "bottleneck_threshold", default=0.85)
        )
        self.anomaly_z: float = float(
            get_config("agent", "analysis_agent", "anomaly_threshold", default=2.0)
        )

        # LLM 客户端 (可选)
        self.llm = llm
        if self.llm is None:
            try:
                self.llm = get_llm(provider=PROVIDER_DEEPSEEK)
            except Exception:
                self.llm = None

    # =========================================================================
    # 主入口
    # =========================================================================

    @try_except(default_return=BottleneckReport())
    def detect_and_report(self, window_hours: int = 24) -> BottleneckReport:
        """
        一键执行: 检测瓶颈 -> 根因分解 -> 建议 -> (可选) LLM 润色建议。
        """
        end = dt.datetime.now()
        start = end - dt.timedelta(hours=window_hours)
        report = BottleneckReport(
            snapshot_time=end,
            window_hours=window_hours,
        )

        # (1) 基础 OEE 数据
        oee_df = self.calc.oee_by_process(start, end)
        wip_df = self.calc.wip_distribution()
        theoretic_df = self.calc.theoretical_capacity_by_process()

        # (2) 利用率四象限拆解
        report.utilization_breakdown = self._breakdown_utilization(start, end)

        # (3) 瓶颈评分
        scored = self._score_bottlenecks(oee_df, wip_df, theoretic_df, start, end)
        report.bottlenecks = scored

        # (4) 对 Top3 瓶颈做根因分解
        top_processes = [b["process"] for b in scored[:3]]
        if not top_processes:
            top_processes = [b["process"] for b in sorted(
                [r for _, r in oee_df.iterrows()],
                key=lambda x: float(x.get("utilization", 0)),
                reverse=True,
            )[:3]]

        report.causes = []
        report.suggestions = []
        for p in top_processes:
            causes = self._decompose_causes(
                p, breakdown=report.utilization_breakdown,
                oee_df=oee_df, wip_df=wip_df,
            )
            report.causes.extend(causes)
            suggestions = self._generate_suggestions(
                p, causes, theoretic_df=theoretic_df
            )
            report.suggestions.extend(suggestions)

        # (5) LLM 增强建议 (若可用)
        if self.llm and self.llm.is_configured:
            new_suggestions = self._llm_enhance_suggestions(report)
            if new_suggestions:
                report.suggestions = new_suggestions
                report.llm_enhanced = True

        logger.info(
            f"瓶颈检测完成: 共识别 {len(report.bottlenecks)} 个瓶颈工序, "
            f"{len(report.causes)} 条根因, {len(report.suggestions)} 项改进建议."
            f" LLM增强: {'✓' if report.llm_enhanced else '本地模板'}"
        )
        return report

    # =========================================================================
    # 利用率四象限拆解
    # =========================================================================

    def _breakdown_utilization(self, s: dt.datetime, e: dt.datetime) -> pd.DataFrame:
        """
        返回每工序在窗口内的时间构成:
          planned_hours, run_h, down_h, pm_h, setup_h, idle_h, utilization,
          down_pct, pm_pct, setup_pct
        """
        total_h = max(1e-6, (e - s).total_seconds() / 3600.0)
        rows = []
        for p in ALL_PROCESSES:
            n = self.calc.equipment_count(p)
            if n <= 0:
                continue
            total_calendar = total_h * n
            # 从 oee_by_process 拉 run/down/pm (已经按工序聚合过)
            oee = self.calc.oee_by_process(s, e)
            row_p = oee[oee["process"] == p]
            run_h = float(row_p["run_hours"].iloc[0]) if not row_p.empty else 0.0
            down_h = float(row_p["down_hours"].iloc[0]) if not row_p.empty else 0.0
            pm_h = float(row_p["pm_hours"].iloc[0]) if not row_p.empty else 0.0
            # Setup 单独补 (oee 把 setup 算到 down 里了, 这里单独拆出来)
            setup_h = float(self._sum_event_duration(p, EVENT_SETUP_START, s, e))
            # 修正 down = down_h - setup_h (避免双计)
            down_h = max(0.0, down_h - setup_h)
            idle_h = max(0.0, total_calendar - run_h - down_h - pm_h - setup_h)
            util = safe_div(run_h, total_calendar, default=0.0)
            rows.append({
                "process": p,
                "process_cn": PROCESS_NAME_CN.get(p, p),
                "equipment_count": n,
                "total_hours": safe_round(total_calendar, 1),
                "run_h": safe_round(run_h, 1),
                "run_pct": safe_round(run_h / total_calendar, 4),
                "down_h": safe_round(down_h, 1),
                "down_pct": safe_round(down_h / total_calendar, 4),
                "pm_h": safe_round(pm_h, 1),
                "pm_pct": safe_round(pm_h / total_calendar, 4),
                "setup_h": safe_round(setup_h, 1),
                "setup_pct": safe_round(setup_h / total_calendar, 4),
                "idle_h": safe_round(idle_h, 1),
                "idle_pct": safe_round(idle_h / total_calendar, 4),
                "utilization": safe_round(util, 4),
            })
        return pd.DataFrame(rows)

    def _sum_event_duration(self, process: str, event_type: str, s, e) -> float:
        sql = f"""
            SELECT COALESCE(SUM(ee.duration_h),0) AS s
            FROM equipment_events ee JOIN equipment eq ON eq.equip_id=ee.equip_id
            WHERE ee.event_type=? AND eq.process=? AND ee.event_time>=? AND ee.event_time<?
        """
        try:
            row = self.db.query_one(
                sql,
                (event_type, process,
                 s.strftime("%Y-%m-%d %H:%M:%S"), e.strftime("%Y-%m-%d %H:%M:%S")),
            )
            return float(row["s"] or 0.0) if row else 0.0
        except Exception:
            return 0.0

    # =========================================================================
    # 瓶颈评分 (组合规则)
    # =========================================================================

    def _score_bottlenecks(
        self,
        oee_df: pd.DataFrame,
        wip_df: pd.DataFrame,
        theoretic_df: pd.DataFrame,
        s: dt.datetime,
        e: dt.datetime,
    ) -> List[Dict[str, Any]]:
        """
        为每工序打瓶颈分 (0~1), 取分数 > 阈值的工序为瓶颈。
        维度权重:
          w_util = 0.40   (利用率超阈值部分)
          w_wip  = 0.25   (WIP 积压偏离均值)
          w_down = 0.20   (停机占比)
          w_tp   = 0.15   (产出/理论 比值 越低分越高)
        """
        items = []
        wip_av = wip_df["wafers"].mean() if len(wip_df) else 1.0
        wip_av = max(1.0, wip_av)

        for p in ALL_PROCESSES:
            op = oee_df[oee_df["process"] == p]
            wp = wip_df[wip_df["process"] == p]
            tp = theoretic_df[theoretic_df["process"] == p]
            if op.empty:
                continue

            util = float(op["utilization"].iloc[0])
            oee = float(op["oee"].iloc[0])
            down_pct = float(op["down_hours"].iloc[0]) / max(1e-6, float(op["planned_hours"].iloc[0]))

            wip = int(wp["wafers"].iloc[0]) if not wp.empty else 0
            # 维度1: utilization
            s_util = max(0.0, min(1.0, (util - self.util_threshold) / max(1e-6, 1 - self.util_threshold) + 0.5))
            # 维度2: wip
            s_wip = max(0.0, min(1.0, (wip / wip_av - 1.0) / 2.0 + 0.5)) if wip_av > 0 else 0.0
            # 维度3: downtime (越高分越高)
            s_down = max(0.0, min(1.0, down_pct * 6))
            # 维度4: 理论产出 vs 实际upc
            if not tp.empty:
                eff_up = float(tp["effective_uph"].iloc[0])
                act_up = float(op["uph"].iloc[0])
                ratio = safe_div(act_up, eff_up, default=1.0)
                s_tp = max(0.0, min(1.0, 1 - ratio))
            else:
                s_tp = 0.0

            score = 0.40 * s_util + 0.25 * s_wip + 0.20 * s_down + 0.15 * s_tp
            items.append({
                "process": p,
                "process_cn": PROCESS_NAME_CN.get(p, p),
                "score": safe_round(score, 4),
                "utilization": safe_round(util, 4),
                "oee": safe_round(oee, 4),
                "wip_wafers": wip,
                "down_hours": safe_round(float(op["down_hours"].iloc[0]), 1),
                # 强制原生 bool, 避免 numpy.bool_ 导致 JSON 序列化失败
                "flag_high_util": bool(util >= self.util_threshold),
                "flag_high_wip": bool(wip > wip_av * 1.5),
                "flag_high_down": bool(down_pct > 0.08),
            })
        items.sort(key=lambda x: x["score"], reverse=True)
        # 取 score >= 0.45 或 前3个 (至少保证3个)
        threshold = 0.45
        passed = [x for x in items if x["score"] >= threshold]
        if len(passed) < 3:
            passed = items[: max(3, len(passed))]
        return passed

    # =========================================================================
    # 根因分解
    # =========================================================================

    def _decompose_causes(
        self,
        process: str,
        breakdown: pd.DataFrame,
        oee_df: pd.DataFrame,
        wip_df: pd.DataFrame,
    ) -> List[BottleneckCause]:
        """按工序生成根因列表。"""
        causes: List[BottleneckCause] = []
        b = breakdown[breakdown["process"] == process]
        o = oee_df[oee_df["process"] == process]
        w = wip_df[wip_df["process"] == process]
        if b.empty:
            return causes
        br = b.iloc[0]
        down_pct = float(br["down_pct"])
        pm_pct = float(br["pm_pct"])
        setup_pct = float(br["setup_pct"])
        idle_pct = float(br["idle_pct"])
        perf = float(o["performance"].iloc[0]) if not o.empty else 0.0
        avail = float(o["availability"].iloc[0]) if not o.empty else 0.0
        wip_w = int(w["wafers"].iloc[0]) if not w.empty else 0

        # 规则: 占比 > 10% 或 最大项 => 根因
        max_dim = max(
            [("DownTime", down_pct), ("PM", pm_pct), ("Setup", setup_pct), ("Idle", idle_pct)],
            key=lambda x: x[1],
        )
        mtbf_target = 48.0
        if down_pct > 0.08 or max_dim[0] == "DownTime":
            mtbf_est = safe_div(1 - down_pct, max(1e-6, down_pct)) * 4  # 粗略估算
            causes.append(BottleneckCause(
                process=process, dimension="DownTime",
                severity_score=min(1.0, down_pct * 5),
                quantitative_indicator=(
                    f"{PROCESS_NAME_CN.get(process, process)}故障停机占比={down_pct*100:.1f}%, "
                    f"估计MTBF={mtbf_est:.0f}h (目标≥{mtbf_target:.0f}h)"
                ),
                detail=f"非计划停机过高, 可用率仅{avail*100:.1f}%, 拉低OEE",
            ))
        if pm_pct > 0.08 or max_dim[0] == "PM":
            causes.append(BottleneckCause(
                process=process, dimension="PM",
                severity_score=min(1.0, pm_pct * 4),
                quantitative_indicator=f"PM占比={pm_pct*100:.1f}%, 预计可通过PM优化压缩至5%以内",
                detail="预防性维护周期偏短或窗口未错峰, 导致有效运行时间不足",
            ))
        if setup_pct > 0.04 or max_dim[0] == "Setup":
            causes.append(BottleneckCause(
                process=process, dimension="Setup",
                severity_score=min(1.0, setup_pct * 10),
                quantitative_indicator=f"换型调试占比={setup_pct*100:.1f}%, 批次切换频繁",
                detail="建议合并同产品批次, 减少配方切换, 推行SMED快速换型",
            ))
        if perf < 0.85 and idle_pct < 0.30:
            causes.append(BottleneckCause(
                process=process, dimension="Performance",
                severity_score=min(1.0, (0.95 - perf) * 3),
                quantitative_indicator=f"性能率仅{perf*100:.1f}% (目标≥85%)",
                detail="实际加工节拍慢于标准, 需核查工艺参数/设备老化/操作人员",
            ))
        if wip_w > 0 and not any(c.dimension == "Capacity" for c in causes):
            causes.append(BottleneckCause(
                process=process, dimension="Capacity",
                severity_score=min(1.0, wip_w / max(1.0, 20000)),
                quantitative_indicator=f"WIP积压={wip_w}片, 前工序入料>本工序有效产出",
                detail="产能缺口: 设备台数不足或OEE过低, 需增机或提升OEE",
            ))
        return causes

    # =========================================================================
    # 改进建议生成 (规则引擎)
    # =========================================================================

    def _generate_suggestions(
        self,
        process: str,
        causes: List[BottleneckCause],
        theoretic_df: pd.DataFrame,
    ) -> List[BottleneckSuggestion]:
        """基于根因生成可操作建议, 每项附预估OEE/产能收益。"""
        sugs: List[BottleneckSuggestion] = []
        theo = theoretic_df[theoretic_df["process"] == process]
        eff_cap = float(theo["effective_wafers_per_week"].iloc[0]) if not theo.empty else 1000.0
        eq_count = int(theo["equipment_count"].iloc[0]) if not theo.empty else 1
        pcn = PROCESS_NAME_CN.get(process, process)

        dims = {c.dimension: c for c in causes}
        if "DownTime" in dims:
            sugs.append(BottleneckSuggestion(
                process=process, category="维护",
                action=f"{pcn}工序: 推行预测性维护(根据振动/温度数据), 增加备品备件安全库存, "
                       f"将 MTBF 提升至 60h+, 降低突发故障频率。",
                expected_improvement={"oee_increase": 0.03, "capacity_increase_pct": 5.0,
                                      "weekly_wafers_gain": int(eff_cap * 0.05)},
                priority=1, effort="M",
            ))
        if "PM" in dims:
            sugs.append(BottleneckSuggestion(
                process=process, category="计划",
                action=f"{pcn}工序: 错峰安排PM (集中到周末/夜班), 延长部分高可靠设备的PM周期 168h→240h "
                       f"并验证良率不下降, 压缩计划停机占比。",
                expected_improvement={"oee_increase": 0.02, "capacity_increase_pct": 3.0,
                                      "weekly_wafers_gain": int(eff_cap * 0.03)},
                priority=1, effort="S",
            ))
        if "Setup" in dims:
            sugs.append(BottleneckSuggestion(
                process=process, category="排产",
                action=f"{pcn}工序: 按产品分组连续排产(同产品连续 3 批再切换), 推行 SMED 快速换型方法论, "
                       f"将换型时间压缩 50%。",
                expected_improvement={"oee_increase": 0.015, "capacity_increase_pct": 2.0,
                                      "weekly_wafers_gain": int(eff_cap * 0.02)},
                priority=2, effort="S",
            ))
        if "Performance" in dims:
            sugs.append(BottleneckSuggestion(
                process=process, category="工艺",
                action=f"{pcn}工序: 重检标准工序时间合理性, 核查TOP5慢批是否共性(某配方/某操作员/某设备), "
                       f"必要时更新标准recipe并培训班组。",
                expected_improvement={"oee_increase": 0.02, "capacity_increase_pct": 2.5,
                                      "weekly_wafers_gain": int(eff_cap * 0.025)},
                priority=2, effort="M",
            ))
        if "Capacity" in dims:
            cap_gain = 15.0 if eq_count <= 0 else safe_round(1.0 / eq_count * 100, 1)
            sugs.append(BottleneckSuggestion(
                process=process, category="设备",
                action=f"{pcn}工序: 短期通过 OEE 三步法(可用性/性能/良率)挖潜(投入级别S); "
                       f"中期评估增加 1~2 台设备(当前 {eq_count} 台), 预计可有效吸收积压 WIP。",
                expected_improvement={"oee_increase": 0.0,
                                      "capacity_increase_pct": cap_gain,
                                      "weekly_wafers_gain": int(eff_cap * 0.15)},
                priority=3, effort="L",
            ))
        return sugs

    # =========================================================================
    # LLM 增强建议
    # =========================================================================

    @try_except(default_return=[])
    def _llm_enhance_suggestions(self, report: BottleneckReport) -> List[BottleneckSuggestion]:
        """
        让 LLM 基于瓶颈数据, 生成更专业的改进建议 JSON, 解析为 BottleneckSuggestion 列表。
        LLM 不可用时返回 [] (保留原建议)。
        """
        if not self.llm or not self.llm.check_available():
            return []
        schema = {
            "suggestions": [{
                "process": "PHOTO",
                "category": "维护/排产/工艺/设备/计划",
                "action": "具体行动建议(中文, 详细可落地)",
                "expected_improvement": {"oee_increase": 0.02, "capacity_increase_pct": 3.0,
                                         "weekly_wafers_gain": 300},
                "priority": 1,
                "effort": "S",
            }]
        }
        prompt = (
            "你是半导体晶圆厂Fab产能优化总监, 擅长运用TOC约束理论/Lean精益/OEE方法论给出可落地的改进建议。\n"
            "以下是当前瓶颈检测数据(JSON):\n"
            f"{json_str(report.to_dict())}\n"
            "请给出5~8条具体、可量化、分优先级的改进建议, 严格按参考schema输出JSON(suggestions数组)。"
            "priority: 1=高紧急且高收益, 2=中, 3=长期/高投入。effort=S(小)/M(中)/L(大)。"
        )
        data = self.llm.chat_json(prompt, schema_hint=schema, max_tokens=2000)
        if not data or "suggestions" not in data:
            return []
        out: List[BottleneckSuggestion] = []
        for s in data["suggestions"]:
            try:
                if not s.get("process") or not s.get("action"):
                    continue
                ei = s.get("expected_improvement", {}) or {}
                out.append(BottleneckSuggestion(
                    process=s["process"],
                    category=str(s.get("category", "其他")),
                    action=str(s["action"]),
                    expected_improvement={
                        "oee_increase": float(ei.get("oee_increase", 0)),
                        "capacity_increase_pct": float(ei.get("capacity_increase_pct", 0)),
                        "weekly_wafers_gain": int(float(ei.get("weekly_wafers_gain", 0))),
                    },
                    priority=min(3, max(1, int(s.get("priority", 2)))),
                    effort=str(s.get("effort", "M")).upper()[:1] or "M",
                ))
            except Exception:
                continue
        return out


# =========================================================================
# 辅助: json.dumps 小工具(避免循环import)
# =========================================================================
import json as _json

def json_str(obj: Any) -> str:
    try:
        return _json.dumps(obj, ensure_ascii=False, default=str, indent=2)
    except Exception:
        return str(obj)


# =============================================================================
# 单例
# =============================================================================

_detector_instance: Optional[BottleneckDetector] = None


def get_detector() -> BottleneckDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = BottleneckDetector()
    return _detector_instance


# =============================================================================
# 自检
# =============================================================================

if __name__ == "__main__":
    det = get_detector()
    r = det.detect_and_report(window_hours=24)
    print("=== 瓶颈工序 (按严重度降序) ===")
    for b in r.bottlenecks:
        print(f"  {b['process_cn']:>6s}  score={b['score']:.2f}  Util={b['utilization']*100:4.1f}%  "
              f"OEE={b['oee']*100:4.1f}%  WIP={b['wip_wafers']:>5d}片")
    print()
    print("=== 根因分解 ===")
    for c in r.causes:
        print(f"  [{c.process:6s}] {c.dimension:11s} (严重度={c.severity_score:.2f}) → {c.quantitative_indicator}")
    print()
    print(f"=== 改进建议 (共{len(r.suggestions)}条, LLM增强={'✓' if r.llm_enhanced else '本地'}) ===")
    for s in sorted(r.suggestions, key=lambda x: (x.priority, -x.expected_improvement.get('capacity_increase_pct', 0))):
        p = "★" * (4 - s.priority)
        gain = s.expected_improvement.get('capacity_increase_pct', 0)
        print(f"  P{s.priority} {p} [{s.category:4s}/{s.effort}] {s.process:6s} "
              f"→ 产能+{gain:.1f}%  {s.action[:70]}...")
    print()
    print("=== 利用率四象限 (前5行) ===")
    print(r.utilization_breakdown[
        ["process","run_pct","down_pct","pm_pct","setup_pct","idle_pct","utilization"]
    ].head().to_string(index=False))

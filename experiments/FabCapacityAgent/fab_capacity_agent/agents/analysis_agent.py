"""
FabCapacityAgent - 分析 Agent (AnalysisAgent)

职责: 基于感知快照做历史趋势分析、OEE 诊断、瓶颈识别
      作为整个 Agent 链路的"大脑-分析层"。

PTA 分工:
  perceive: 从 context.snapshot 取上游感知结果, 拉历史 daily_output 时序
  think:    趋势分析 + Z-score 异常检测 + 瓶颈根因分解 (调用 BottleneckDetector)
  act:      生成结构化分析报告 (含 LLM 文字摘要), 写入 context.analysis_report
"""

import os
import sys
import datetime as dt
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from agents.base_agent import BaseAgent, AgentContext
from services.capacity_calculator import CapacityCalculator, get_calculator
from services.bottleneck_detector import BottleneckDetector, get_detector
from models.capacity import DailyOutputDAO
from utils.helpers import (
    get_logger, try_except, safe_round,
    detect_anomalies, parse_datetime,
)
from utils.constants import AGENT_ANALYSIS, ALL_PROCESSES, PROCESS_NAME_CN
from utils.llm_client import LLMClient

logger = get_logger("AnalysisAgent", level="INFO")


class AnalysisAgent(BaseAgent):
    """分析 Agent: 历史趋势 + OEE 诊断 + 瓶颈识别。"""

    AGENT_TYPE = AGENT_ANALYSIS
    AGENT_NAME_CN = "分析Agent"

    def __init__(
        self,
        calc: Optional[CapacityCalculator] = None,
        detector: Optional[BottleneckDetector] = None,
        llm: Optional[LLMClient] = None,
        use_llm: Optional[bool] = None,
    ) -> None:
        super().__init__(name=AGENT_ANALYSIS, llm=llm, use_llm=use_llm)
        self.calc = calc or get_calculator()
        self.detector = detector or get_detector()
        self.daily_dao = DailyOutputDAO()

    # =========================================================================
    # perceive
    # =========================================================================
    def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """
        从上游 snapshot + DB 拉取分析所需数据:
          - 上游 snapshot
          - 近 30 天 daily_output 时序
          - 近 30 天 cycle_time 时序
          - 近 7 天停机帕累托
        """
        snap = context.snapshot or {}
        # 兼容: 上游可能是 dict 或 CapacitySnapshot 对象
        if hasattr(snap, "to_dict"):
            snap = snap.to_dict()

        history_days = int(context.extra.get("history_days", 30))
        self.logger.info(f"拉取近 {history_days} 天历史数据用于分析...")

        # daily_output 时序
        daily_df = self.daily_dao.recent(days=history_days)
        # cycle_time 时序
        ct_df = self.calc.cycle_time_series(days=history_days)
        # 停机帕累托 (近 7 天)
        end = dt.datetime.now()
        start = end - dt.timedelta(days=7)
        pareto_df = self.calc.downtime_pareto(start, end, top_n=10)

        return {
            "snapshot": snap,
            "daily_history": daily_df.to_dict(orient="records"),
            "cycle_time_series": ct_df.to_dict(orient="records"),
            "downtime_pareto": pareto_df.to_dict(orient="records"),
            "history_days": history_days,
        }

    # =========================================================================
    # think
    # =========================================================================
    def think(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心分析:
          1) OEE / 产出 趋势分析 (线性斜率)
          2) Z-score 异常检测 (产出 & cycle_time)
          3) 调用 BottleneckDetector 做根因分解
        """
        # ---- 1. 趋势分析 ----
        daily_list = perception.get("daily_history", [])
        output_series = [float(d.get("output_wafers", 0)) for d in daily_list]
        oee_series = [float(d.get("avg_oee", 0)) for d in daily_list]

        trend = self._compute_trend(output_series, oee_series)

        # ---- 2. 异常检测 ----
        ct_list = perception.get("cycle_time_series", [])
        ct_series = [float(c.get("avg_cycle_time_h", 0)) for c in ct_list]
        anomalies = self._detect_anomalies(daily_list, ct_list)

        # ---- 3. 瓶颈根因分解 ----
        bottleneck_report = self.detector.detect_and_report(window_hours=24)
        bottlenecks = bottleneck_report.bottlenecks
        causes = [c.__dict__ for c in bottleneck_report.causes]

        return {
            "trend": trend,
            "anomalies": anomalies,
            "bottlenecks": bottlenecks,
            "bottleneck_causes": causes,
            "downtime_pareto": perception.get("downtime_pareto", []),
            "snapshot": perception.get("snapshot", {}),
        }

    # =========================================================================
    # act
    # =========================================================================
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成分析报告 (含 LLM 文字摘要)。
        """
        # 构造给 LLM 的 KPI 数据
        trend = decision.get("trend", {})
        kpi_data = {
            "oee": trend.get("oee_series", []),
            "daily_output": trend.get("output_series", []),
        }

        # LLM 摘要 (不可用走本地模板)
        summary_text = ""
        if self.llm:
            try:
                summary_text = self.llm.summarize_trend(
                    kpi_data, period_desc=f"近{trend.get('history_days', 30)}天"
                )
            except Exception as exc:
                self.logger.warning(f"LLM 趋势摘要失败: {exc}")

        if not summary_text:
            # 本地兜底模板
            oee_slope = trend.get("oee_slope", 0)
            output_slope = trend.get("output_slope", 0)
            oee_dir = "上升" if oee_slope > 0.001 else ("下降" if oee_slope < -0.001 else "平稳")
            output_dir = "上升" if output_slope > 0.5 else ("下降" if output_slope < -0.5 else "平稳")
            bn_top = decision.get("bottlenecks", [])[:3]
            bn_text = ", ".join(
                f"{PROCESS_NAME_CN.get(b.get('process'), b.get('process'))}"
                f"(Util={b.get('utilization', 0)*100:.1f}%)"
                for b in bn_top
            )
            summary_text = (
                f"【本地分析摘要】\n"
                f"· OEE 趋势: {oee_dir} (斜率={oee_slope:+.4f}/天)\n"
                f"· 产出趋势: {output_dir} (斜率={output_slope:+.2f}片/天)\n"
                f"· 检测到异常点 {len(decision.get('anomalies', {}).get('output_anomalies', []))} 个\n"
                f"· 瓶颈工序: {bn_text or '无明显瓶颈'}\n"
                f"· 建议: 优先关注瓶颈工序的 OEE 三要素分解, 制定专项改善计划。"
            )

        report = {
            "agent": self.AGENT_NAME_CN,
            "trend": trend,
            "anomalies": decision.get("anomalies", {}),
            "bottlenecks": decision.get("bottlenecks", []),
            "bottleneck_causes": decision.get("bottleneck_causes", []),
            "downtime_pareto": decision.get("downtime_pareto", []),
            "summary_text": summary_text,
            "llm_enhanced": bool(self.llm and self.llm.is_configured),
            "status": "ok",
        }
        return report

    # =========================================================================
    # 内部工具
    # =========================================================================

    def _compute_trend(self, output_series: List[float], oee_series: List[float]) -> Dict[str, Any]:
        """用 numpy polyfit 计算线性斜率。"""
        import numpy as np
        result = {
            "output_series": output_series,
            "oee_series": oee_series,
            "output_slope": 0.0,
            "oee_slope": 0.0,
            "output_avg": 0.0,
            "oee_avg": 0.0,
            "history_days": len(output_series),
        }
        if len(output_series) >= 3:
            x = np.arange(len(output_series))
            try:
                result["output_slope"] = float(np.polyfit(x, output_series, 1)[0])
                result["output_avg"] = float(np.mean(output_series))
            except Exception:
                pass
        if len(oee_series) >= 3:
            x = np.arange(len(oee_series))
            try:
                result["oee_slope"] = float(np.polyfit(x, oee_series, 1)[0])
                result["oee_avg"] = float(np.mean(oee_series))
            except Exception:
                pass
        return result

    def _detect_anomalies(self, daily_list: List[Dict], ct_list: List[Dict]) -> Dict[str, Any]:
        """Z-score 异常检测。"""
        import pandas as pd
        result = {"output_anomalies": [], "cycle_time_anomalies": []}
        try:
            if len(daily_list) >= 7:
                df = pd.DataFrame(daily_list)
                if "output_wafers" in df.columns:
                    s = pd.Series(df["output_wafers"], dtype=float)
                    mask = detect_anomalies(s, threshold=2.0)
                    for i, m in mask.items():
                        if m:
                            result["output_anomalies"].append({
                                "date": str(df.iloc[i].get("stat_date", "")),
                                "value": float(s.iloc[i]),
                                "type": "产出异常",
                            })
            if len(ct_list) >= 7:
                df = pd.DataFrame(ct_list)
                if "avg_cycle_time_h" in df.columns:
                    s = pd.Series(df["avg_cycle_time_h"], dtype=float)
                    mask = detect_anomalies(s, threshold=2.0)
                    for i, m in mask.items():
                        if m:
                            result["cycle_time_anomalies"].append({
                                "date": str(df.iloc[i].get("stat_date", "")),
                                "value": float(s.iloc[i]),
                                "type": "CycleTime异常",
                            })
        except Exception as exc:
            self.logger.warning(f"异常检测失败: {exc}")
        return result

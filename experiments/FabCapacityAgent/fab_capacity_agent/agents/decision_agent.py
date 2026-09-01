"""
FabCapacityAgent - 决策 Agent (DecisionAgent)

职责: 基于分析报告, 生成产能预测、排产建议、What-If 决策方案
      作为整个 Agent 链路的"大脑-决策层"。

PTA 分工:
  perceive: 从 context.analysis_report 取上游分析结果
  think:    调用 Predictor 做 7/30 天预测 + 调用 WhatIfSimulator 做情景对比
  act:      生成决策方案 (含排产建议+改进建议+预测曲线), 写入 context.decision_plan
"""

import os
import sys
import datetime as dt
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from agents.base_agent import BaseAgent, AgentContext
from services.predictor import Predictor, get_predictor, ForecastResult
from services.what_if_simulator import WhatIfSimulator, get_simulator, ScenarioConfig
from utils.helpers import get_logger, try_except, safe_round
from utils.constants import (
    AGENT_DECISION, ALL_PROCESSES, PROCESS_NAME_CN, ALL_PRODUCTS, PRODUCT_NAME_CN,
)
from utils.llm_client import LLMClient

logger = get_logger("DecisionAgent", level="INFO")


class DecisionAgent(BaseAgent):
    """决策 Agent: 预测 + 排产建议 + What-If 方案。"""

    AGENT_TYPE = AGENT_DECISION
    AGENT_NAME_CN = "决策Agent"

    def __init__(
        self,
        predictor: Optional[Predictor] = None,
        simulator: Optional[WhatIfSimulator] = None,
        llm: Optional[LLMClient] = None,
        use_llm: Optional[bool] = None,
    ) -> None:
        super().__init__(name=AGENT_DECISION, llm=llm, use_llm=use_llm)
        self.predictor = predictor or get_predictor()
        self.simulator = simulator or get_simulator()

    # =========================================================================
    # perceive
    # =========================================================================
    def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """取上游分析报告 + 用户查询 (若有)。"""
        analysis = context.analysis_report or {}
        # 兼容 dict / 对象
        if hasattr(analysis, "to_dict"):
            analysis = analysis.to_dict()

        return {
            "analysis": analysis,
            "user_query": context.user_query,
            "snapshot": context.snapshot if isinstance(context.snapshot, dict)
                         else (context.snapshot.to_dict() if context.snapshot else {}),
        }

    # =========================================================================
    # think
    # =========================================================================
    def think(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心决策:
          1) 7天短期预测 (生产排产用)
          2) 30天中长期预测 (产能规划用)
          3) What-If 7个预设情景对比
          4) 基于瓶颈给出排产建议
        """
        # ---- 1. 预测 ----
        self.logger.info("生成 7 天 & 30 天预测...")
        forecast_7d = self.predictor.forecast_output(
            horizon_days=7, history_days=60, use_llm=bool(self.llm)
        )
        forecast_30d = self.predictor.forecast_output(
            horizon_days=30, history_days=90, use_llm=bool(self.llm)
        )

        # ---- 2. What-If 情景对比 ----
        self.logger.info("运行 What-If 情景模拟...")
        presets = self.simulator.preset_scenarios()
        scenario_df = self.simulator.compare_scenarios(presets)
        scenarios = scenario_df.to_dict(orient="records")

        # ---- 3. 排产建议 (基于瓶颈+预测) ----
        bottlenecks = perception.get("analysis", {}).get("bottlenecks", [])
        schedule_advice = self._build_schedule_advice(
            forecast_7d, bottlenecks
        )

        return {
            "forecast_7d": forecast_7d.summary(),
            "forecast_30d": forecast_30d.summary(),
            "forecast_7d_detail": forecast_7d.to_dataframe().to_dict(orient="records"),
            "forecast_30d_detail": forecast_30d.to_dataframe().to_dict(orient="records"),
            "scenarios": scenarios,
            "schedule_advice": schedule_advice,
            "bottlenecks": bottlenecks,
        }

    # =========================================================================
    # act
    # =========================================================================
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终决策方案。"""
        # LLM 增强: 让 LLM 基于全量决策给出一段自然语言总结
        llm_summary = ""
        if self.llm:
            try:
                import json
                prompt = (
                    "你是半导体Fab产能规划总监。请基于以下决策数据, 用不超过300字给出:\n"
                    "1) 未来7天产能风险预警\n"
                    "2) 推荐的Top3优化方案及预期收益\n"
                    "3) 排产优先级建议\n\n"
                    f"决策数据(JSON摘要):\n{json.dumps({k: v for k, v in decision.items() if k != 'forecast_30d_detail'}, ensure_ascii=False, default=str)[:2000]}\n"
                )
                llm_summary = self.llm.chat(prompt, max_tokens=600, temperature=0.4) or ""
            except Exception as exc:
                self.logger.warning(f"LLM 决策摘要失败: {exc}")

        if not llm_summary:
            # 本地兜底
            f7 = decision.get("forecast_7d", {})
            f30 = decision.get("forecast_30d", {})
            scs = decision.get("scenarios", [])
            best_sc = max(
                [s for s in scs if s.get("name") != "Baseline"],
                key=lambda x: float(x.get("delta_pct", 0)),
                default={},
            )
            llm_summary = (
                f"【本地决策摘要】\n"
                f"· 7天预测总量: {f7.get('total_predicted_wafers', 0):,}片 (MAPE={f7.get('mape_pct', 0)}%)\n"
                f"· 30天预测总量: {f30.get('total_predicted_wafers', 0):,}片\n"
                f"· 最优情景: {best_sc.get('name', 'N/A')} "
                f"(Δ={best_sc.get('delta_pct', 0)*100:+.2f}%, 风险={best_sc.get('risk_level', 'L')})\n"
                f"· 建议: 优先实施OEE改善(短期) + 评估增机方案(中期)"
            )

        plan = {
            "agent": self.AGENT_NAME_CN,
            "forecast_7d": decision.get("forecast_7d", {}),
            "forecast_30d": decision.get("forecast_30d", {}),
            "forecast_7d_detail": decision.get("forecast_7d_detail", []),
            "forecast_30d_detail": decision.get("forecast_30d_detail", []),
            "scenarios": decision.get("scenarios", []),
            "schedule_advice": decision.get("schedule_advice", []),
            "llm_summary": llm_summary,
            "llm_enhanced": bool(self.llm and self.llm.is_configured),
            "status": "ok",
        }
        return plan

    # =========================================================================
    # 内部: 排产建议
    # =========================================================================

    def _build_schedule_advice(
        self,
        forecast: ForecastResult,
        bottlenecks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        基于瓶颈 + 预测生成排产建议项。

        每项:
          {priority, action, target_process, expected_effect, timeframe}
        """
        advices: List[Dict[str, Any]] = []
        # 取预测均值
        avg_pred = forecast.summary().get("avg_daily_predicted", 0)

        # 1) 瓶颈工序建议
        for i, bn in enumerate(bottlenecks[:3]):
            p = bn.get("process", "")
            util = float(bn.get("utilization", 0))
            wip = int(bn.get("wip_wafers", 0))
            priority = i + 1
            if util > 0.85:
                action = (
                    f"{PROCESS_NAME_CN.get(p, p)}利用率已达{util*100:.1f}%, "
                    f"建议本周期不安排新产品试产, 集中产能消化WIP"
                )
            elif wip > 5000:
                action = (
                    f"{PROCESS_NAME_CN.get(p, p)}积压{wip}片, "
                    f"建议追加夜班人力/延长设备运行窗口, 加速消化"
                )
            else:
                action = f"关注{PROCESS_NAME_CN.get(p, p)}工序产能匹配, 维持当前排产节奏"
            advices.append({
                "priority": priority,
                "target_process": p,
                "action": action,
                "expected_effect": f"预计可缓解 {PROCESS_NAME_CN.get(p, p)} WIP {max(1, wip//10)} 片/天",
                "timeframe": "7天内" if priority <= 2 else "30天内",
            })

        # 2) 产能缺口预警
        if avg_pred > 0:
            target_daily = 1000  # 假设目标日产出1000片
            gap = target_daily - avg_pred
            if gap > 50:
                advices.append({
                    "priority": 1,
                    "target_process": "ALL",
                    "action": (
                        f"预测日均产出{avg_pred:.0f}片, 低于目标{target_daily}片, "
                        f"缺口{gap:.0f}片/天, 建议评估紧急增机或外协方案"
                    ),
                    "expected_effect": f"补齐产能缺口 {gap*7:.0f} 片/周",
                    "timeframe": "立即",
                })

        # 3) 周末排产建议
        advices.append({
            "priority": 3,
            "target_process": "ALL",
            "action": "周末设备PM错峰安排, 避开生产高峰, 减少 PM 对周产能的影响",
            "expected_effect": "预计可释放 3~5% 周产能",
            "timeframe": "本周",
        })

        return advices

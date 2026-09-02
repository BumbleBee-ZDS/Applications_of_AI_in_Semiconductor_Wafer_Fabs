"""
FabCapacityAgent - 执行 Agent (ExecutionAgent)

职责: 把决策方案转化为可视化输出 / 落库 / 报告
      作为整个 Agent 链路的"手脚"。

PTA 分工:
  perceive: 从 context.decision_plan 取决策方案
  think:    把决策方案格式化为可视化友好的结构 (Markdown 报告 + KPI 卡片数据)
  act:      调用 LLM 生成完整 Markdown 报告, 落库到 agent_logs, 写入 context.execution_output
"""

import os
import sys
import datetime as dt
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from agents.base_agent import BaseAgent, AgentContext
from models.capacity import AgentLogDAO
from models.database import get_db
from utils.helpers import get_logger, try_except, safe_round, ensure_dir, resolve_path
from utils.constants import (
    AGENT_EXECUTION, ALL_PROCESSES, PROCESS_NAME_CN,
    PRODUCT_NAME_CN, KPI_NAME_CN,
)
from utils.llm_client import LLMClient

logger = get_logger("ExecutionAgent", level="INFO")


class ExecutionAgent(BaseAgent):
    """执行 Agent: 生成报告 + 落库 + 可视化输出。"""

    AGENT_TYPE = AGENT_EXECUTION
    AGENT_NAME_CN = "执行Agent"

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        use_llm: Optional[bool] = None,
    ) -> None:
        super().__init__(name=AGENT_EXECUTION, llm=llm, use_llm=use_llm)
        self.log_dao = AgentLogDAO()

    # =========================================================================
    # perceive
    # =========================================================================
    def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """取上游决策方案 + 快照 + 分析报告。"""
        decision = context.decision_plan or {}
        if hasattr(decision, "to_dict"):
            decision = decision.to_dict()

        # snapshot 可能是 PerceptionAgent 输出的 {"snapshot": {...}, "anomalies":..., "summary_text":...}
        # 也可能是直接的 CapacitySnapshot dict, 兼容两种
        snapshot_raw = context.snapshot
        if hasattr(snapshot_raw, "to_dict"):
            snapshot = snapshot_raw.to_dict()
        elif isinstance(snapshot_raw, dict):
            # 检查是否包了一层 "snapshot"
            if "snapshot" in snapshot_raw and isinstance(snapshot_raw["snapshot"], dict):
                snapshot = snapshot_raw["snapshot"]
            else:
                snapshot = snapshot_raw
        else:
            snapshot = {}

        # analysis 同样可能包了一层
        analysis_raw = context.analysis_report
        if hasattr(analysis_raw, "to_dict"):
            analysis = analysis_raw.to_dict()
        elif isinstance(analysis_raw, dict):
            analysis = analysis_raw
        else:
            analysis = {}

        return {
            "decision": decision,
            "snapshot": snapshot,
            "analysis": analysis,
            "run_id": context.run_id,
        }

    # =========================================================================
    # think
    # =========================================================================
    def think(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        把决策方案格式化为:
          - KPI 卡片数据 (供前端 st.metric 直接渲染)
          - Markdown 报告骨架
          - 改进建议清单
        """
        snap = perception.get("snapshot", {})
        decision = perception.get("decision", {})
        analysis = perception.get("analysis", {})
        # 顶层 run_id (Orchestrator 注入), 透传给报告骨架
        run_id = perception.get("run_id", "") or ""

        # KPI 卡片
        kpi_cards = {
            "overall_oee": safe_round(float(snap.get("overall_oee", 0)) * 100, 2),
            "wip_total": int(snap.get("wip_total_wafers", 0)),
            "daily_output": int(snap.get("daily_output_24h", 0)),
            "avg_cycle_time": safe_round(float(snap.get("avg_cycle_time_h", 0)), 1),
            "bottleneck_top1": (snap.get("bottleneck_rank") or ["N/A"])[0],
            "forecast_7d_total": int(decision.get("forecast_7d", {}).get("total_predicted_wafers", 0)),
            "forecast_30d_total": int(decision.get("forecast_30d", {}).get("total_predicted_wafers", 0)),
        }

        # 改进建议 (合并 analysis + decision)
        suggestions: List[Dict[str, Any]] = []
        # 从 analysis.bottleneck_causes 拿根因
        for cause in (analysis.get("bottleneck_causes") or [])[:5]:
            suggestions.append({
                "type": "根因",
                "process": cause.get("process", ""),
                "dimension": cause.get("dimension", ""),
                "indicator": cause.get("quantitative_indicator", ""),
                "severity": safe_round(float(cause.get("severity_score", 0)), 2),
            })
        # 从 decision.schedule_advice 拿排产建议
        for adv in (decision.get("schedule_advice") or [])[:5]:
            suggestions.append({
                "type": "排产建议",
                "process": adv.get("target_process", ""),
                "action": adv.get("action", ""),
                "priority": adv.get("priority", 3),
                "timeframe": adv.get("timeframe", ""),
            })

        # Markdown 报告骨架 (显式传入 run_id, 避免 decision 中缺失导致 N/A)
        markdown_skeleton = self._build_markdown_skeleton(
            snap, analysis, decision, kpi_cards, suggestions, run_id=run_id
        )

        return {
            "kpi_cards": kpi_cards,
            "suggestions": suggestions,
            "markdown_skeleton": markdown_skeleton,
            "bottlenecks": analysis.get("bottlenecks", []),
            "scenarios": decision.get("scenarios", []),
            "run_id": run_id,
        }

    # =========================================================================
    # act
    # =========================================================================
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终输出:
          1) 调用 LLM 生成完整 Markdown 报告 (不可用走骨架兜底)
          2) 落库到 agent_logs (审计追踪)
          3) 返回结构化输出
        """
        run_id = decision.get("run_id", "unknown")
        kpi_cards = decision.get("kpi_cards", {})
        skeleton = decision.get("markdown_skeleton", "")

        # LLM 增强报告
        final_report = skeleton
        llm_enhanced = False
        if self.llm and self.llm.is_configured:
            try:
                snap_dict = decision.get("kpi_cards", {})
                bottlenecks = decision.get("bottlenecks", [])
                suggestions = decision.get("suggestions", [])

                # 复用 LLMClient 的领域专用接口
                llm_report = self.llm.generate_capacity_report(
                    snapshot=snap_dict,
                    bottlenecks=bottlenecks,
                    anomalies=suggestions,
                )
                # 给 LLM 生成的报告统一追加溯源 header (Run ID + 生成时间 + LLM 标记),
                # 确保 Run ID 不会因 LLM 自由发挥而丢失
                header = (
                    f"> 生成时间: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  "
                    f"| Run ID: `{run_id}`  | LLM增强: ✓\n\n"
                )
                final_report = header + llm_report
                llm_enhanced = True
            except Exception as exc:
                self.logger.warning(f"LLM 报告生成失败, 走骨架兜底: {exc}")
                final_report = skeleton

        # 落库到 agent_logs
        try:
            self.log_dao.insert(
                run_id=run_id,
                agent_type=self.AGENT_TYPE,
                stage="act",
                status="success",
                input_snapshot={"kpi_cards": kpi_cards},
                output_result={"report_length": len(final_report)},
                duration_ms=self.last_duration_ms,
            )
        except Exception as exc:
            self.logger.warning(f"日志落库失败: {exc}")

        # 自动保存报告到文件 (可选)
        report_path = None
        try:
            save_report = bool(__import__("utils.helpers", fromlist=["get_config"]).get_config(
                "agent", "execution_agent", "auto_save_report", default=False
            ))
            if save_report:
                reports_dir = ensure_dir(resolve_path("data/reports"))
                filename = f"report_{run_id}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                report_path = reports_dir / filename
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(final_report)
                self.logger.info(f"报告已保存: {report_path}")
        except Exception as exc:
            self.logger.warning(f"报告保存失败: {exc}")

        return {
            "agent": self.AGENT_NAME_CN,
            "kpi_cards": kpi_cards,
            "suggestions": decision.get("suggestions", []),
            "bottlenecks": decision.get("bottlenecks", []),
            "scenarios": decision.get("scenarios", []),
            "final_report": final_report,
            "report_path": str(report_path) if report_path else None,
            "llm_enhanced": llm_enhanced,
            "run_id": run_id,
            "status": "ok",
        }

    # =========================================================================
    # 内部: Markdown 骨架
    # =========================================================================

    def _build_markdown_skeleton(
        self,
        snap: Dict[str, Any],
        analysis: Dict[str, Any],
        decision: Dict[str, Any],
        kpi_cards: Dict[str, Any],
        suggestions: List[Dict[str, Any]],
        run_id: str = "",
    ) -> str:
        """本地兜底的 Markdown 报告骨架。"""
        # run_id 优先用显式传入, 其次从 decision 取, 都没有则 N/A
        rid = run_id or decision.get("run_id", "") or "N/A"
        lines = [
            "# 📋 FabCapacityAgent 产能分析报告",
            f"\n> 生成时间: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> Run ID: `{rid}`",
            "\n---\n",
            "## 1. 执行摘要\n",
            f"- 全厂 OEE: **{kpi_cards.get('overall_oee', 0):.2f}%**",
            f"- 24h 产出: **{kpi_cards.get('daily_output', 0):,}** 片",
            f"- WIP 总量: **{kpi_cards.get('wip_total', 0):,}** 片",
            f"- 平均 CycleTime: **{kpi_cards.get('avg_cycle_time', 0):.1f}** h",
            f"- 瓶颈工序 Top1: **{PROCESS_NAME_CN.get(kpi_cards.get('bottleneck_top1', ''), kpi_cards.get('bottleneck_top1', 'N/A'))}**",
            "\n## 2. 产能预测\n",
            f"- 未来 7 天预测总量: **{kpi_cards.get('forecast_7d_total', 0):,}** 片",
            f"- 未来 30 天预测总量: **{kpi_cards.get('forecast_30d_total', 0):,}** 片",
        ]

        # 瓶颈工序
        bns = analysis.get("bottlenecks", [])
        if bns:
            lines.append("\n## 3. 瓶颈诊断\n")
            lines.append("| 工序 | 利用率 | OEE | WIP(片) | 严重度 |")
            lines.append("|------|--------|-----|---------|--------|")
            for b in bns[:5]:
                lines.append(
                    f"| {PROCESS_NAME_CN.get(b.get('process',''), b.get('process',''))} "
                    f"| {b.get('utilization',0)*100:.1f}% "
                    f"| {b.get('oee',0)*100:.1f}% "
                    f"| {b.get('wip_wafers',0):,} "
                    f"| {b.get('score',0):.2f} |"
                )

        # What-If 情景
        scs = decision.get("scenarios", [])
        if scs:
            lines.append("\n## 4. What-If 情景对比\n")
            lines.append("| 情景 | 周产能(片) | Δ(片) | Δ% | OEE | 风险 |")
            lines.append("|------|-----------|-------|-----|-----|------|")
            for s in scs:
                lines.append(
                    f"| {s.get('name','')} "
                    f"| {s.get('total_wafers_per_week',0):,.0f} "
                    f"| {s.get('delta_wafers',0):+,.0f} "
                    f"| {s.get('delta_pct',0)*100:+.2f}% "
                    f"| {s.get('overall_oee',0)*100:.2f}% "
                    f"| {s.get('risk_level','L')} |"
                )

        # 建议
        if suggestions:
            lines.append("\n## 5. 改进建议\n")
            for i, s in enumerate(suggestions[:8], 1):
                if s.get("type") == "根因":
                    lines.append(
                        f"{i}. **[{s.get('process','')}/{s.get('dimension','')}]** "
                        f"{s.get('indicator','')}"
                    )
                else:
                    lines.append(
                        f"{i}. **[P{s.get('priority',3)}/{s.get('timeframe','')}]** "
                        f"{s.get('action','')}"
                    )

        lines.append("\n---\n")
        lines.append(f"*报告由 FabCapacityAgent 自动生成 (LLM增强: {'✓' if self.llm and self.llm.is_configured else '本地模板'})*")
        return "\n".join(lines)

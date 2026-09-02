"""执行 Agent：风险分级（L1~L4）+ 人工审批 + 执行。

风险分级规则：
- 诊断建议 HOLD → 至少 L3；
- 派工涉及 URGENT / HIGH 批次 → 至少 L3；
- 调度模型声明 L3/L4 → 取更高值；
- 多重高风险因素叠加（≥2 项）→ L4。

执行策略：
- L1 / L2：低风险，系统自动执行；
- L3：中高风险，需 2 人审批；
- L4：高风险，需 3 人审批。

审批单与执行动作均写入审计日志，保证全链路可追溯。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from utils.helpers import now_iso

RISK_LEVELS: tuple[str, ...] = ("L1", "L2", "L3", "L4")
APPROVERS_NEEDED: dict[int, int] = {1: 0, 2: 0, 3: 2, 4: 3}  # L3→2 人，L4→3 人
APPROVAL_DECISIONS: dict[str, str] = {
    "APPROVED": "✅ 批准",
    "REJECTED": "❌ 拒绝",
    "REVIEW": "🔄 复审",
}


def _risk_num(level: Any) -> int:
    """把 L1~L4 字符串转成整数，失败时默认 2。"""
    try:
        return int(str(level).strip().upper().replace("L", ""))
    except (TypeError, ValueError):
        return 2


def classify_risk(strategy: dict[str, Any], diagnoses: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """按 L1~L4 对策略做风险分级。

    Args:
        strategy: 调度策略（recommended_dispatch 需含 lot_priority 字段）。
        diagnoses: 诊断结果列表（含 hold_equipment 字段）。

    Returns:
        (风险等级字符串, 判定依据列表)。
    """
    level = 1
    reasons: list[str] = []
    dispatch = strategy.get("recommended_dispatch", []) or []

    hold_events = [d for d in diagnoses if d.get("hold_equipment")]
    if hold_events:
        level = max(level, 3)
        reasons.append(f"诊断建议 HOLD {len(hold_events)} 台设备")

    urgent_high = [d for d in dispatch if d.get("lot_priority", "NORMAL") in ("URGENT", "HIGH")]
    if urgent_high:
        level = max(level, 3)
        reasons.append(f"涉及 {len(urgent_high)} 条 URGENT/HIGH 优先级派工")

    llm_level = _risk_num(strategy.get("risk_level", "L1"))
    if llm_level > level:
        level = llm_level
        reasons.append(f"调度模型声明风险等级 {strategy.get('risk_level')}")

    if strategy.get("requires_approval") and level < 2:
        level = 2
        reasons.append("调度模型要求人工确认")

    # 多重高风险因素叠加 → L4
    factors = (
        int(bool(hold_events))
        + int(bool(urgent_high))
        + int(llm_level >= 3)
        + int(len(dispatch) >= 4)
    )
    if factors >= 2 and level < 4:
        level = 4
        reasons.append("多重高风险因素叠加（HOLD/高优先级/模型声明/派工规模≥4）")

    return f"L{level}", reasons


class ApprovalStore:
    """审批单存储（内存实现，MVP 足够；生产环境应换数据库）。

    通过 :func:`utils.helpers.init_session_state` 挂载到 st.session_state，
    实现页面间共享。
    """

    def __init__(self) -> None:
        self._tickets: dict[str, dict[str, Any]] = {}
        self._seq = 0

    def create_ticket(
        self,
        strategy: dict[str, Any],
        risk_level: str,
        required_approvals: int,
        audit: Any = None,
        trace_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """创建一张待审批单。"""
        self._seq += 1
        dispatch = strategy.get("recommended_dispatch", []) or []
        ticket = {
            "ticket_id": f"TKT-{datetime.now():%Y%m%d-%H%M%S}-{self._seq:03d}",
            "strategy_id": strategy.get("strategy_id", "-"),
            "risk_level": risk_level,
            "required_approvals": required_approvals,
            "approvals": [],
            "status": "PENDING",
            "created_at": now_iso(),
            "executed": False,
            "dispatch_count": len(dispatch),
            "dispatch_preview": [f"{d.get('lot_id')}→{d.get('equipment_id')}" for d in dispatch[:5]],
        }
        self._tickets[ticket["ticket_id"]] = ticket
        if audit is not None:
            audit.log_event(
                trace_id=trace_id, agent="execution_agent", action="create_approval_ticket",
                input_summary=f"策略 {ticket['strategy_id']} 风险 {risk_level}",
                decision="PENDING",
                evidence={"ticket_id": ticket["ticket_id"], "required_approvals": required_approvals},
            )
        return ticket

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        """按 ID 获取审批单。"""
        return self._tickets[ticket_id]

    def submit_decision(self, ticket_id: str, approver: str, comment: str, decision: str) -> dict[str, Any]:
        """提交一次审批决定（批准/拒绝/复审）。

        - 同一审批人重复提交将被忽略；
        - 任一拒绝 → 单据 REJECTED；
        - 批准人数达到 required_approvals → 单据 APPROVED；
        - 复审不计数，保持 PENDING。
        """
        ticket = self._tickets[ticket_id]
        if ticket["status"] != "PENDING":
            return ticket
        if any(a["approver"] == approver for a in ticket["approvals"]):
            return ticket
        ticket["approvals"].append({
            "approver": approver,
            "comment": comment,
            "decision": decision,
            "timestamp": now_iso(),
        })
        if decision == "REJECTED":
            ticket["status"] = "REJECTED"
        else:
            approved = sum(1 for a in ticket["approvals"] if a["decision"] == "APPROVED")
            if approved >= ticket["required_approvals"]:
                ticket["status"] = "APPROVED"
        return ticket

    def mark_executed(self, ticket_id: str, audit: Any = None, trace_id: Optional[str] = None) -> dict[str, Any]:
        """标记审批单对应策略已执行。"""
        ticket = self._tickets[ticket_id]
        ticket["executed"] = True
        ticket["status"] = "EXECUTED"
        if audit is not None:
            audit.log_event(
                trace_id=trace_id, agent="execution_agent", action="execute_approved_strategy",
                input_summary=f"执行审批单 {ticket_id} 对应策略 {ticket['strategy_id']}",
                decision="EXECUTED",
                evidence={"ticket_id": ticket_id, "dispatch_count": ticket["dispatch_count"]},
            )
        return ticket

    def pending_tickets(self) -> list[dict[str, Any]]:
        """返回全部待审批单。"""
        return [t for t in self._tickets.values() if t["status"] == "PENDING"]

    def all_tickets(self) -> list[dict[str, Any]]:
        """返回全部审批单（含历史）。"""
        return list(self._tickets.values())


def execute(
    strategy: dict[str, Any],
    diagnoses: list[dict[str, Any]],
    store: Optional[ApprovalStore] = None,
    audit: Any = None,
    trace_id: Optional[str] = None,
) -> dict[str, Any]:
    """执行入口：L1/L2 自动执行；L3/L4 生成审批单等待审批。

    Args:
        strategy: 调度策略。
        diagnoses: 诊断结果列表。
        store: ApprovalStore 实例（L3/L4 必需）。
        audit: AuditAgent 实例（用于留痕）。
        trace_id: 全链路追踪 ID。

    Returns:
        执行结果：status（EXECUTED / PENDING_APPROVAL）、risk_level、ticket_id 等。
    """
    risk_level, reasons = classify_risk(strategy, diagnoses)
    if _risk_num(risk_level) <= 2:
        result = {
            "status": "EXECUTED",
            "risk_level": risk_level,
            "reasons": reasons,
            "executed_dispatch": strategy.get("recommended_dispatch", []),
            "ticket_id": None,
            "message": "低风险策略已自动执行",
        }
        if audit is not None:
            audit.log_event(
                trace_id=trace_id, agent="execution_agent", action="auto_execute",
                input_summary=f"策略 {strategy.get('strategy_id')}",
                decision="AUTO_EXECUTED",
                evidence={"risk_level": risk_level, "dispatch_count": len(result["executed_dispatch"])},
            )
    else:
        required = APPROVERS_NEEDED[_risk_num(risk_level)]
        ticket = store.create_ticket(strategy, risk_level, required, audit=audit, trace_id=trace_id) if store else None
        result = {
            "status": "PENDING_APPROVAL",
            "risk_level": risk_level,
            "reasons": reasons,
            "ticket_id": ticket["ticket_id"] if ticket else None,
            "required_approvals": required,
            "message": f"风险 {risk_level}，需 {required} 人审批后执行",
        }
    return result

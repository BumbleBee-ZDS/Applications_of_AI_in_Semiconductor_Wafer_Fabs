"""✅ 人工审批：策略详情 / 审批流（L3 需 2 人、L4 需 3 人）/ 执行。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from agents import execution_agent
from utils import helpers

st.set_page_config(page_title="3 人工审批", page_icon="✅", layout="wide")
helpers.init_session_state()

st.title("✅ 人工审批与执行")

# 展示上一步操作的结果提示（提交审批/执行后经 st.rerun 回来显示）
if "approval_msg" in st.session_state:
    msg = st.session_state.pop("approval_msg")
    if msg["type"] == "success":
        st.success(msg["text"])
    elif msg["type"] == "error":
        st.error(msg["text"])
    else:
        st.info(msg["text"])

strategy = st.session_state.get("strategy")
if not strategy:
    st.info("暂无待审批策略，请先到 **2 Agent 分析** 页运行全链路。")
    st.stop()

diagnoses = st.session_state.get("diagnoses") or []
audit = st.session_state["audit_agent"]
store = st.session_state["approval_store"]
trace_id = st.session_state.get("last_trace_id")

# ---------- 策略详情 + 风险分级 ----------
risk_level, reasons = execution_agent.classify_risk(strategy, diagnoses)
needed = execution_agent.APPROVERS_NEEDED[int(risk_level[1])]

st.subheader("📋 策略详情")
rc = st.columns(5)
rc[0].metric("策略 ID", strategy["strategy_id"])
rc[1].metric("风险等级", risk_level)
rc[2].metric("所需审批", f"{needed} 人" if needed else "自动执行")
rc[3].metric("OTD 预估", f"{strategy['otd_estimate_min']} min")
rc[4].metric("派工条数", len(strategy["recommended_dispatch"]))

st.markdown("**风险判定依据**：" + ("；".join(reasons) if reasons else "无特殊风险因子，默认 L1"))
st.markdown(f"**质量风险说明**：{strategy['quality_risk_note']}")

df_disp = pd.DataFrame([
    {"批次": d.get("lot_id"), "目标设备": d.get("equipment_id"), "动作": d.get("action"), "理由": d.get("reason")}
    for d in strategy["recommended_dispatch"]
])
st.dataframe(df_disp, use_container_width=True, hide_index=True)

# ---------- 执行入口 ----------
st.subheader("⚙️ 执行")
if st.session_state.get("execution_result"):
    res = st.session_state["execution_result"]
    if res["status"] == "EXECUTED":
        st.success(f"✅ 已自动执行（风险 {res['risk_level']}）：{res['message']}，共 {len(res['executed_dispatch'])} 条派工")
    else:
        st.info(f"⏳ 待审批：{res['message']}")

if needed == 0:
    if st.button("⚡ 自动执行（L1/L2 低风险）", type="primary"):
        res = execution_agent.execute(strategy, diagnoses, store=store, audit=audit, trace_id=trace_id)
        st.session_state["execution_result"] = res
        st.session_state["approval_msg"] = {"type": "success", "text": f"✅ 自动执行完成（风险 {res['risk_level']}）"}
        st.rerun()
else:
    if st.button(f"📝 生成审批单（需 {needed} 人审批）", type="primary"):
        res = execution_agent.execute(strategy, diagnoses, store=store, audit=audit, trace_id=trace_id)
        st.session_state["execution_result"] = res
        st.session_state["approval_msg"] = {"type": "info", "text": f"已生成审批单 {res['ticket_id']}，需 {needed} 人审批"}
        st.rerun()

# ---------- 审批表单 ----------
st.subheader("🗳 审批表单")
pending = store.pending_tickets()
if not pending:
    st.success("当前无待审批单。")
else:
    def _ticket_label(tid: str) -> str:
        t = store.get_ticket(tid)
        approved = sum(1 for a in t["approvals"] if a["decision"] == "APPROVED")
        return f"{tid} | 策略 {t['strategy_id']} | 风险 {t['risk_level']} | 已批 {approved}/{t['required_approvals']}"

    chosen_id = st.selectbox("选择待审批单", [t["ticket_id"] for t in pending], format_func=_ticket_label)
    ticket = store.get_ticket(chosen_id)

    with st.expander("查看审批单详情", expanded=True):
        st.json({k: v for k, v in ticket.items() if k != "approvals"})
        if ticket["approvals"]:
            st.markdown("**已有审批记录**：")
            st.dataframe(pd.DataFrame(ticket["approvals"]), use_container_width=True, hide_index=True)

    with st.form("approval_form"):
        approver = st.text_input("审批人姓名")
        comment = st.text_area("审批意见")
        decision = st.radio(
            "审批决定",
            ["APPROVED", "REJECTED", "REVIEW"],
            format_func=lambda d: execution_agent.APPROVAL_DECISIONS[d],
            horizontal=True,
        )
        submitted = st.form_submit_button("提交审批")

    if submitted:
        if not approver.strip():
            st.warning("请填写审批人姓名")
        else:
            updated = store.submit_decision(chosen_id, approver.strip(), comment, decision)
            audit.log_event(
                trace_id, "execution_agent", "approval_submit",
                f"审批单 {chosen_id}，审批人 {approver.strip()}",
                decision,
                evidence={"ticket_id": chosen_id, "ticket_status": updated["status"]},
            )
            if updated["status"] == "APPROVED":
                st.session_state["approval_msg"] = {"type": "success", "text": f"🎉 审批完成（{updated['required_approvals']} 人已批准），可执行该策略"}
            elif updated["status"] == "REJECTED":
                st.session_state["approval_msg"] = {"type": "error", "text": "❌ 该审批单已被拒绝"}
            else:
                approved_now = sum(1 for a in updated["approvals"] if a["decision"] == "APPROVED")
                st.session_state["approval_msg"] = {"type": "info", "text": f"已记录审批意见（已批准 {approved_now}/{updated['required_approvals']} 人）"}
            st.rerun()

# ---------- 执行已批准策略 ----------
st.subheader("🔄 执行已批准策略")
approved_not_executed = [t for t in store.all_tickets() if t["status"] == "APPROVED" and not t["executed"]]
if not approved_not_executed:
    st.info("暂无已批准待执行的审批单。")
for t in approved_not_executed:
    if st.button(f"⚙️ 执行 {t['ticket_id']}（策略 {t['strategy_id']}）", key=t["ticket_id"]):
        store.mark_executed(t["ticket_id"], audit=audit, trace_id=trace_id)
        st.session_state["approval_msg"] = {"type": "success", "text": f"✅ 策略 {t['strategy_id']} 已执行并写入审计日志"}
        st.rerun()

# ---------- 历史审批表 ----------
st.subheader("📜 审批历史")
all_tickets = store.all_tickets()
if all_tickets:
    df_hist = pd.DataFrame([
        {
            "审批单": t["ticket_id"],
            "策略": t["strategy_id"],
            "风险": t["risk_level"],
            "需审批": t["required_approvals"],
            "状态": t["status"],
            "已执行": "✅" if t["executed"] else "-",
            "创建时间": t["created_at"],
            "派工预览": "；".join(t["dispatch_preview"]),
        }
        for t in all_tickets
    ])

    def _color_status(row: pd.Series) -> list[str]:
        colors = {"APPROVED": "#d4f7d4", "EXECUTED": "#d1e7ff", "REJECTED": "#f8d7da", "PENDING": "#fff3cd"}
        return [f"background-color: {colors.get(row['状态'], '')}"] * len(row)

    st.dataframe(df_hist.style.apply(_color_status, axis=1), use_container_width=True, hide_index=True)

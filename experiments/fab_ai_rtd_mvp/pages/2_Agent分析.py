"""🔍 Agent 分析：Perception → Diagnosis(RAG) → Scheduling → RL 全链路。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from agents import (
    diagnosis_agent,
    execution_agent,
    perception_agent,
    rl_simulator,
    scheduling_agent,
)
from data import factory_simulator
from utils import helpers, knowledge_base

st.set_page_config(page_title="2 Agent 分析", page_icon="🔍", layout="wide")
helpers.init_session_state()

st.title("🔍 Agent 全链路分析")
st.caption("一键运行：感知（阈值）→ RAG 诊断（DeepSeek v4-pro）→ 调度（DeepSeek v4-pro）→ RL 仿真评估。")

with st.spinner("正在向量化工艺知识库（千问 Embedding）..."):
    kb_info = knowledge_base.ensure_indexed()
st.caption(f"📚 知识库：{kb_info['mode']} 共 {kb_info['docs']} 篇文档，向量维度 {kb_info.get('dim', '-')}")
if kb_info.get("error"):
    st.warning(f"⚠️ 千问 Embedding 暂不可用，已回退本地伪向量：{kb_info['error']}")


def _run_pipeline() -> None:
    """执行全链路并把结果写入 session_state（供各页面共享）。"""
    if st.session_state["factory_state"] is None:
        st.session_state["factory_state"] = factory_simulator.generate_factory_state()
    state = st.session_state["factory_state"]
    audit = st.session_state["audit_agent"]
    trace_id = helpers.generate_trace_id()
    st.session_state["last_trace_id"] = trace_id

    # ① 感知
    events = perception_agent.perceive(state)
    st.session_state["events"] = events
    audit.log_event(
        trace_id, "perception_agent", "scan_factory_state",
        f"扫描 {len(state['equipment'])} 台设备、{len(state['lots'])} 个批次、{len(state['alarms'])} 条告警",
        f"检出 {len(events)} 个异常事件",
        evidence={"equipment_count": len(state["equipment"]), "lot_count": len(state["lots"]), "event_count": len(events)},
    )

    # ② 诊断（千问 RAG + DeepSeek v4-pro）
    with st.spinner("🩺 诊断 Agent：千问 RAG 检索 Top-3 + DeepSeek v4-pro 根因分析..."):
        diagnoses = diagnosis_agent.diagnose_events(events, top_k=3)
    st.session_state["diagnoses"] = diagnoses
    audit.log_event(
        trace_id, "diagnosis_agent", "rag_diagnose",
        f"对 {len(events)} 个事件执行 RAG Top-3 检索与根因分析",
        f"完成 {len(diagnoses)} 份诊断报告",
        evidence={"diagnosis_count": len(diagnoses)},
    )

    # ③ 调度（DeepSeek v4-pro）
    with st.spinner("🧭 调度 Agent：DeepSeek v4-pro 生成派工策略..."):
        strategy = scheduling_agent.build_strategy(state, diagnoses)
    st.session_state["strategy"] = strategy
    audit.log_event(
        trace_id, "scheduling_agent", "generate_dispatch_strategy",
        f"输入：工厂状态压缩摘要 + {len(diagnoses)} 份诊断摘要",
        f"生成策略 {strategy['strategy_id']}（风险 {strategy['risk_level']}，派工 {len(strategy['recommended_dispatch'])} 条）",
        evidence={"strategy_id": strategy["strategy_id"], "dispatch_count": len(strategy["recommended_dispatch"])},
    )

    # ④ RL 仿真
    candidates = [strategy] + rl_simulator.perturb_strategy(strategy, state=state, n_variants=3)
    rl_results = rl_simulator.evaluate_multiple(candidates, state)
    st.session_state["rl_results"] = rl_results
    audit.log_event(
        trace_id, "rl_simulator", "evaluate_strategies",
        f"评估 {len(candidates)} 条候选策略（1 原始 + 3 扰动）",
        f"最优策略 {rl_results[0]['strategy_id']}，reward={rl_results[0]['reward']}",
        evidence={"candidate_count": len(candidates), "best_strategy_id": rl_results[0]["strategy_id"], "best_reward": rl_results[0]["reward"]},
    )

    st.session_state["execution_result"] = None  # 重置上一次执行结果
    st.success(f"✅ 全链路完成，trace_id：{trace_id}")


if st.button("🚀 运行全链路（调用真实 LLM）", type="primary"):
    _run_pipeline()

# ================= ① 感知结果 =================
st.subheader("① 感知 Agent（阈值扫描）")
events = st.session_state.get("events") or []
if not events:
    st.info("尚未检出异常事件。可在 **1 实时监控** 页注入异常后回到本页运行全链路。")
else:
    df_ev = pd.DataFrame([
        {
            "事件 ID": ev["event_id"],
            "类型": ev["event_type"],
            "级别": ev["severity"],
            "设备": ev["equipment_id"],
            "批次": ev.get("current_lot") or "-",
            "描述": ev["description"],
        }
        for ev in events
    ])

    def _color_sev(row: pd.Series) -> list[str]:
        colors = {"CRITICAL": "#f8d7da", "HIGH": "#f8d7da", "MEDIUM": "#fff3cd", "LOW": "#d1e7ff"}
        return [f"background-color: {colors.get(row['级别'], '')}"] * len(row)

    st.dataframe(df_ev.style.apply(_color_sev, axis=1), use_container_width=True, hide_index=True)

# ================= ② 诊断结果 =================
st.subheader("② 诊断 Agent（RAG Top-3 + DeepSeek v4-pro）")
diagnoses = st.session_state.get("diagnoses") or []
if not diagnoses:
    st.info("运行全链路后展示诊断报告。")
for d in diagnoses:
    with st.expander(
        f"{d['event_id']} {d['equipment_id']} {d['severity']} · 平均置信度 {d.get('confidence_avg', 0):.2f}",
        expanded=False,
    ):
        if d.get("fallback_reason"):
            st.warning(f"⚠️ LLM 调用失败，已使用规则降级：{d['fallback_reason']}")
        st.markdown(f"**事件描述**：{d.get('description', '-')}")
        st.markdown("**根因（置信度进度条）**：")
        for rc in d["root_causes"]:
            conf = min(1.0, max(0.0, float(rc.get("confidence", 0.5))))
            st.progress(conf, text=f"根因：{rc['cause']}（置信度 {conf:.0%}）")
        st.markdown(f"**质量影响**：{d['quality_impact']}")
        st.markdown(f"**RTD 调度建议**：{d['rtd_suggestion']}")
        st.markdown(
            f"**需人工确认**：{'✅ 是' if d.get('human_confirmation_required') else '❌ 否'}　"
            f"**建议设备 HOLD**：{'✅ 是' if d.get('hold_equipment') else '❌ 否'}"
        )
        st.markdown("**知识库引用（RAG）**：")
        for kb in d.get("retrieved_kb", []):
            st.markdown(f"- `{kb['doc_id']}` {kb['title']}（相似度 {kb['score']:.3f}）")

# ================= ③ 调度结果 =================
st.subheader("③ 调度 Agent（DeepSeek v4-pro）")
strategy = st.session_state.get("strategy")
if not strategy:
    st.info("运行全链路后展示派工策略。")
else:
    if strategy.get("llm_error"):
        st.warning(f"⚠️ DeepSeek 调用失败，已使用启发式策略：{strategy['llm_error']}")
    st.caption(f"策略来源：{strategy.get('source', '-')}")
    sc = st.columns(5)
    sc[0].metric("策略 ID", strategy["strategy_id"])
    sc[1].metric("声明风险", strategy["risk_level"])
    sc[2].metric("需人工确认", "✅ 是" if strategy["requires_approval"] else "❌ 否")
    sc[3].metric("OTD 预估", f"{strategy['otd_estimate_min']} min")
    sc[4].metric("派工条数", len(strategy["recommended_dispatch"]))
    constraints_text = " / ".join(strategy["constraints_checked"]) or "无"
    st.markdown(f"**已检查约束**：{constraints_text}")
    st.markdown(f"**质量风险说明**：{strategy['quality_risk_note']}")
    df_disp = pd.DataFrame([
        {"批次": d.get("lot_id"), "目标设备": d.get("equipment_id"), "动作": d.get("action"), "理由": d.get("reason")}
        for d in strategy["recommended_dispatch"]
    ])
    st.dataframe(df_disp, use_container_width=True, hide_index=True)

# ================= ④ RL 结果 =================
st.subheader("④ RL 仿真评估（启发式奖励）")
rl_results = st.session_state.get("rl_results") or []
if not rl_results:
    st.info("运行全链路后展示 RL 排名。")
else:
    df_rl = pd.DataFrame([
        {k: r[k] for k in ("strategy_id", "variant", "utilization", "cycle_time", "otd", "quality_risk", "qtime_penalty", "reward")}
        for r in rl_results
    ])
    best_reward = df_rl["reward"].max()

    def _hl(row: pd.Series) -> list[str]:
        return ["background-color: #d4f7d4"] * len(row) if row["reward"] == best_reward else [""] * len(row)

    st.dataframe(df_rl.style.apply(_hl, axis=1), use_container_width=True, hide_index=True)
    st.markdown(f"🏆 **最优策略**：`{rl_results[0]['strategy_id']}`（reward = {rl_results[0]['reward']}）")
    st.caption(
        "奖励函数：利用率 +1.0×负载、周期 +0.8×覆盖率、OTD +1.5×交期满足、"
        "质量风险 −2.0×风险分、Q-Time 违例 −10.0/次"
    )

# ================= ⑤ 执行风险预判 =================
st.subheader("⚖️ 执行 Agent 风险预判（L1~L4）")
if strategy:
    level, reasons = execution_agent.classify_risk(strategy, diagnoses)
    needed = execution_agent.APPROVERS_NEEDED[int(level[1])]
    st.markdown(f"**风险等级**：`{level}` → {'⚡ 自动执行' if needed == 0 else f'需 {needed} 人审批'}")
    st.markdown("**判定依据**：" + ("；".join(reasons) if reasons else "无特殊风险因子"))
    try:
        st.page_link("pages/3_人工审批.py", label="➡️ 前往 3 人工审批 页执行策略", icon="✅")
    except Exception:
        st.info("下一步：前往左侧导航 **3 人工审批** 页执行策略。")
else:
    st.info("运行全链路后展示风险分级。")

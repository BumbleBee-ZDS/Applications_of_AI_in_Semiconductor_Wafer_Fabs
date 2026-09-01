"""📜 审计日志：全链路追溯 + JSON 详情查看 + 导出。"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from utils import helpers

st.set_page_config(page_title="4 审计日志", page_icon="📜", layout="wide")
helpers.init_session_state()

st.title("📜 审计日志（全链路追溯）")

audit = st.session_state["audit_agent"]
logs = audit.all_logs()

if not logs:
    st.info("暂无审计日志。请先在 **2 Agent 分析** 页运行全链路，再到 **3 人工审批** 页提交审批/执行。")
else:
    trace_ids = sorted({log["trace_id"] for log in logs})
    col1, col2 = st.columns([1.2, 2.4])
    with col1:
        trace_filter = st.selectbox("按 trace_id 筛选", ["全部"] + trace_ids)
    with col2:
        st.caption(f"共 {len(logs)} 条日志")

    filtered = logs if trace_filter == "全部" else audit.get_trace(trace_filter)

    st.subheader("📋 日志列表")
    df_logs = pd.DataFrame([
        {
            "日志 ID": log["log_id"],
            "时间": log["timestamp"],
            "trace_id": log["trace_id"],
            "Agent": log["agent"],
            "动作": log["action"],
            "决策": log["decision"],
            "输入摘要": log["input_summary"],
        }
        for log in filtered
    ])
    st.dataframe(df_logs, use_container_width=True, hide_index=True)

    st.subheader("🔍 单条记录 JSON 详情")
    chosen = st.selectbox("选择日志记录", [log["log_id"] for log in filtered])
    record = next(log for log in filtered if log["log_id"] == chosen)
    st.json(record)

    st.subheader("⬇️ 导出")
    st.download_button(
        "下载完整审计日志 (JSON)",
        data=audit.to_json(),
        file_name=f"audit_log_{datetime.now():%Y%m%d_%H%M%S}.json",
        mime="application/json",
    )

"""NL2SQL 页面。

输入自然语言问题，生成 Oracle 方言 SQL，
展示召回表、JOIN 路径、上下文与置信度。

对应ResNet端到端推理输出层：检索增强 + 图谱约束 + LLM 生成。
"""
from __future__ import annotations

import streamlit as st

from ui.streamlit_app.services import get_nl2sql_service_cached
from fabgraph.models.semantic import NL2SQLRequest


def render_nl2sql_page() -> None:
    """渲染 NL2SQL 页面。"""
    st.header("NL2SQL")

    # 输入区
    with st.container():
        question = st.text_area(
            "自然语言问题",
            "",
            height=100,
            key="nl2sql_question",
            placeholder="例如：统计各产品线最近 30 天的平均良率，按良率降序排列",
        )
        col1, col2, col3 = st.columns(3)
        top_k = col1.number_input(
            "召回表数 Top K", min_value=1, max_value=20, value=5, step=1,
            key="nl2sql_topk",
        )

    if not question.strip():
        st.info("请输入自然语言问题")
        return

    service = get_nl2sql_service_cached()
    if st.button("生成 SQL", type="primary", key="nl2sql_generate_btn"):
        try:
            with st.spinner("生成中..."):
                req = NL2SQLRequest(question=question, top_k=int(top_k))
                resp = service.generate(req)
            st.session_state["nl2sql_response"] = resp
        except Exception as e:
            st.error(f"生成失败: {e}")
            st.session_state["nl2sql_response"] = None

    resp = st.session_state.get("nl2sql_response")
    if resp is None:
        return

    # 状态指标
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("置信度", f"{resp.confidence:.4f}")
    col2.metric("召回表数", len(resp.related_tables))
    col3.metric("JOIN 路径数", len(resp.join_paths))
    col4.metric("校验通过", "是" if resp.is_validated else "否")

    if resp.mock_mode:
        st.warning("当前为 Mock 模式（未调用真实 LLM）")

    # SQL 展示
    st.subheader("生成 SQL")
    st.code(resp.sql, language="sql")

    # 复制按钮（Streamlit 原生无复制 API，用文本框兜底）
    st.text_area("可编辑复制", resp.sql, height=150, key="nl2sql_sql_editable")

    # 召回表
    st.divider()
    st.subheader("召回的相关表")
    if resp.related_tables:
        st.write(resp.related_tables)
    else:
        st.info("无召回表")

    # JOIN 路径
    st.divider()
    st.subheader("JOIN 路径")
    if resp.join_paths:
        join_rows = []
        for jp in resp.join_paths:
            join_rows.append({
                "起始表": jp.get("start", ""),
                "终止表": jp.get("end", ""),
                "路径": " -> ".join(jp.get("path", [])),
                "JOIN 条件": " AND ".join(jp.get("conditions", [])),
                "总权重": round(jp.get("weight", 0.0), 3),
            })
        st.dataframe(join_rows, use_container_width=True)
    else:
        st.info("无 JOIN 路径（单表或不可达）")

    # 上下文
    with st.expander("LLM 上下文（调试用）"):
        st.json(resp.context)

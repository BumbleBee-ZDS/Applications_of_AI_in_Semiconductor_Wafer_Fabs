"""语义检索页面。

提供自然语言问题输入，展示表/字段召回结果与图谱扩展命中。

对应ResNet检索增强：向量近邻 + 图谱邻居联合召回。
"""
from __future__ import annotations

import streamlit as st

from ui.streamlit_app.services import (
    get_semantic_service_cached,
    get_metadata_repo_cached,
)


def render_search_page() -> None:
    """渲染语义检索页面。"""
    st.header("语义检索")

    # 输入区
    with st.container():
        col1, col2 = st.columns([4, 1])
        question = col1.text_input(
            "自然语言问题", "", key="search_question",
            placeholder="例如：查询最近一周良率低于 95% 的批次",
        )
        top_k = col2.number_input(
            "Top K", min_value=1, max_value=30, value=5, step=1, key="search_topk"
        )
        expand = st.checkbox(
            "启用图谱 1-hop 扩展", value=True, key="search_expand"
        )
        only_tables = st.checkbox(
            "仅返回表级结果", value=False, key="search_tables_only"
        )

    if not question.strip():
        st.info("请输入自然语言问题")
        return

    service = get_semantic_service_cached()
    try:
        with st.spinner("检索中..."):
            if only_tables:
                results = service.search_tables(
                    question, top_k=int(top_k), expand=False
                )
            else:
                results = service.search(
                    question, top_k=int(top_k), expand=expand
                )
    except Exception as e:
        st.error(f"检索失败: {e}")
        return

    if not results:
        st.warning("未召回任何结果")
        return

    # 结果摘要
    st.subheader(f"召回 {len(results)} 条结果")

    # 结果表格
    rows = []
    for r in results:
        rows.append({
            "类型": r.node_type.value,
            "表名": r.table_name,
            "字段名": r.column_name,
            "相似度": round(r.score, 4),
            "扩展来源": r.expanded_from or "直接命中",
            "文本": r.item.text if r.item else "",
        })
    st.dataframe(rows, use_container_width=True)

    # 明细
    st.divider()
    st.subheader("结果详情")
    repo = get_metadata_repo_cached()
    for i, r in enumerate(results[:10], 1):
        title = f"#{i} [{r.node_type.value}] {r.table_name}"
        if r.column_name:
            title += f".{r.column_name}"
        title += f"  (score={r.score:.4f})"
        with st.expander(title):
            if r.expanded_from:
                st.caption(f"图谱扩展来源: {r.expanded_from}")
            if r.item and r.item.text:
                st.text(f"嵌入文本: {r.item.text}")
            # 若命中表，展示表结构
            if r.table_name and r.node_type.value == "table":
                table = repo.get_table_by_name(r.table_name)
                if table:
                    st.text(f"表描述: {table.description}")
                    st.text(f"行数: {table.row_count}  标签: {', '.join(table.tags)}")
                    col_rows = [
                        {
                            "字段": c.column_name,
                            "类型": c.data_type,
                            "语义类型": c.semantic_type.value,
                            "语义标签": c.semantic_label,
                            "置信度": f"{c.confidence:.2f}",
                        }
                        for c in table.columns[:20]
                    ]
                    st.dataframe(col_rows, use_container_width=True)


    # 重建索引入口
    st.divider()
    with st.expander("索引管理"):
        st.caption("若元数据更新，可重建向量索引。")
        if st.button("重建索引", key="reindex_btn", type="primary"):
            try:
                with st.spinner("重建中..."):
                    n = service.index_metadata()
                st.success(f"已索引 {n} 项")
                st.rerun()
            except Exception as e:
                st.error(f"重建失败: {e}")

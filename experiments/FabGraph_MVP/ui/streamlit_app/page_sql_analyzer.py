"""SQL 分析页面。

支持单条 SQL 分析与批量分析历史 SQL，展示提取的语义提示。

对应ResNet残差块：每条历史 SQL 贡献增量语义信号。
"""
from __future__ import annotations

from collections import Counter

import streamlit as st

from ui.streamlit_app.services import get_sql_analyzer_cached, get_metadata_repo_cached


def render_sql_analyzer_page() -> None:
    """渲染 SQL 分析页面。"""
    st.header("SQL 语义分析")

    tab_single, tab_batch = st.tabs(["单条分析", "批量分析"])

    # ---------------- 单条分析 ----------------
    with tab_single:
        _render_single_tab()

    # ---------------- 批量分析 ----------------
    with tab_batch:
        _render_batch_tab()


def _render_single_tab() -> None:
    """渲染单条 SQL 分析标签页。"""
    sql = st.text_area(
        "SQL 文本",
        "",
        height=150,
        key="an_sql",
        placeholder="例如：SELECT a.lot_id, b.yield FROM LOT_HISTORY a JOIN YIELD_SUMMARY b ON a.lot_id = b.lot_id WHERE b.yield < 0.95",
    )

    if not sql.strip():
        st.info("请输入 SQL")
        return

    if not st.button("分析", type="primary", key="an_single_btn"):
        return

    analyzer = get_sql_analyzer_cached()
    try:
        with st.spinner("分析中..."):
            hints = analyzer.analyze(sql)
    except Exception as e:
        st.error(f"分析失败: {e}")
        return

    if not hints:
        st.warning("未提取到任何语义提示")
        return

    st.subheader(f"提取到 {len(hints)} 条语义提示")

    # 按类型统计
    type_counts = Counter(h.hint_type for h in hints)
    cols = st.columns(len(type_counts))
    for col, (ht, cnt) in zip(cols, type_counts.items()):
        col.metric(ht, cnt)

    # 提示明细表
    st.divider()
    st.subheader("提示明细")
    rows = [
        {
            "类型": h.hint_type,
            "表名": h.table_name,
            "字段名": h.column_name,
            "提示值": h.hint_value,
            "置信度": round(h.confidence, 3),
            "LLM 推断": "是" if h.inferred_by_llm else "否",
        }
        for h in hints
    ]
    st.dataframe(rows, use_container_width=True)

    # 按类型分组展示
    st.divider()
    st.subheader("按类型分组")
    by_type: dict[str, list] = {}
    for h in hints:
        by_type.setdefault(h.hint_type, []).append(h)
    for ht, items in by_type.items():
        with st.expander(f"{ht}（{len(items)} 条）"):
            for h in items:
                st.text(
                    f"  {h.table_name}.{h.column_name} -> {h.hint_value} "
                    f"(conf={h.confidence:.2f})"
                )


def _render_batch_tab() -> None:
    """渲染批量分析标签页。"""
    repo = get_metadata_repo_cached()
    sqls = repo.get_sql_history()

    if not sqls:
        st.info("无历史 SQL")
        return

    st.caption(f"共 {len(sqls)} 条历史 SQL")

    # 类别过滤
    categories = list({s["category"] for s in sqls})
    cat_filter = st.selectbox(
        "按类别过滤", ["全部"] + categories, key="an_batch_cat"
    )
    show_sqls = (
        sqls if cat_filter == "全部"
        else [s for s in sqls if s["category"] == cat_filter]
    )

    if not st.button("批量分析", type="primary", key="an_batch_btn"):
        return

    analyzer = get_sql_analyzer_cached()
    try:
        with st.spinner(f"分析 {len(show_sqls)} 条 SQL..."):
            hints = analyzer.analyze_batch(show_sqls)
    except Exception as e:
        st.error(f"批量分析失败: {e}")
        return

    # 概览指标
    col1, col2, col3 = st.columns(3)
    col1.metric("SQL 数", len(show_sqls))
    col2.metric("提示总数", len(hints))
    col3.metric("类别数", len(set(h.hint_type for h in hints)))

    # 按类型统计
    type_counts = Counter(h.hint_type for h in hints)
    st.divider()
    st.subheader("按提示类型统计")
    type_rows = [{"类型": ht, "数量": cnt} for ht, cnt in type_counts.most_common()]
    st.dataframe(type_rows, use_container_width=True)

    # 按表统计
    table_counts = Counter(h.table_name for h in hints if h.table_name)
    st.subheader("涉及表 Top 10")
    if table_counts:
        top_rows = [
            {"表名": t, "提示数": c}
            for t, c in table_counts.most_common(10)
        ]
        st.dataframe(top_rows, use_container_width=True)
    else:
        st.info("无表级提示")

    # 提示明细（限制前 50 条）
    with st.expander(f"提示明细（前 50 / {len(hints)}）"):
        rows = [
            {
                "类型": h.hint_type,
                "表名": h.table_name,
                "字段名": h.column_name,
                "提示值": h.hint_value,
                "置信度": round(h.confidence, 3),
            }
            for h in hints[:50]
        ]
        st.dataframe(rows, use_container_width=True)

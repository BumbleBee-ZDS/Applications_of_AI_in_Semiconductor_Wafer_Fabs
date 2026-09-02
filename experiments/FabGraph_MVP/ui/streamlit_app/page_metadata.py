"""元数据浏览页面。"""
from __future__ import annotations

import streamlit as st

from ui.streamlit_app.services import get_metadata_repo_cached


def render_metadata_page() -> None:
    """渲染元数据浏览页面。"""
    st.header("元数据浏览")
    repo = get_metadata_repo_cached()

    # 表列表
    tables = repo.get_tables()
    st.subheader(f"表列表（共 {len(tables)} 张）")

    # 搜索框
    search = st.text_input("搜索表名", "", key="table_search")
    filtered = [
        t for t in tables
        if not search or search.upper() in t.table_name.upper()
    ]

    # 展示为表格
    table_data = [
        {
            "表名": t.table_name,
            "Schema": t.schema_name,
            "描述": t.description[:50] + "..." if len(t.description) > 50 else t.description,
            "行数": t.row_count,
            "字段数": len(t.columns),
            "标签": ", ".join(t.tags),
        }
        for t in filtered
    ]
    st.dataframe(table_data, use_container_width=True)

    # 选中表详情
    if filtered:
        selected = st.selectbox(
            "选择表查看详情",
            [t.table_name for t in filtered],
            key="table_select",
        )
        if selected:
            table = repo.get_table_by_name(selected)
            if table:
                st.subheader(f"表详情: {table.table_name}")
                col1, col2, col3 = st.columns(3)
                col1.metric("字段数", len(table.columns))
                col2.metric("行数", table.row_count)
                col3.metric("标签", len(table.tags))

                st.text(f"描述: {table.description}")

                # 字段表
                st.subheader("字段列表")
                col_data = [
                    {
                        "位置": c.position,
                        "字段名": c.column_name,
                        "类型": c.data_type,
                        "可空": "是" if c.nullable else "否",
                        "语义类型": c.semantic_type.value,
                        "语义标签": c.semantic_label,
                        "描述": c.description[:40] + "..." if len(c.description) > 40 else c.description,
                        "置信度": f"{c.confidence:.2f}",
                    }
                    for c in table.columns
                ]
                st.dataframe(col_data, use_container_width=True)

    # 存储过程
    st.divider()
    st.subheader("存储过程")
    procs = repo.get_procedures()
    proc_data = [
        {
            "过程名": p.procedure_name,
            "描述": p.description[:50] + "..." if len(p.description) > 50 else p.description,
            "输入表": ", ".join(p.input_tables),
            "输出表": ", ".join(p.output_tables),
        }
        for p in procs
    ]
    st.dataframe(proc_data, use_container_width=True)

    # SQL 历史
    st.divider()
    st.subheader("SQL 历史")
    sqls = repo.get_sql_history()
    st.caption(f"共 {len(sqls)} 条历史 SQL")
    categories = list({s["category"] for s in sqls})
    cat_filter = st.selectbox(
        "按类别过滤", ["全部"] + categories, key="sql_cat"
    )
    show_sqls = sqls if cat_filter == "全部" else [
        s for s in sqls if s["category"] == cat_filter
    ]
    for s in show_sqls[:20]:
        with st.expander(f"[{s['category']}] SQL #{s['sql_id']}"):
            st.code(s["sql"], language="sql")

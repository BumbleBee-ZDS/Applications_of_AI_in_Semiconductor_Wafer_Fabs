"""图谱可视化页面。

展示 Schema Graph / Lineage Graph / JOIN Graph / 社区检测结果。
使用 pyvis 渲染交互式 HTML。

对应ResNet注意力可视化：直观展示节点间语义与血缘连接。
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from ui.streamlit_app.services import get_build_result_cached
from ui.streamlit_app.graph_viz import render_graph, render_join_graph


def render_graph_page() -> None:
    """渲染图谱可视化页面。"""
    st.header("图谱可视化")

    result = get_build_result_cached()
    tab_schema, tab_join, tab_lineage, tab_community = st.tabs(
        ["Schema Graph", "JOIN Graph", "Lineage Graph", "社区检测"]
    )

    # ---------------- Schema Graph ----------------
    with tab_schema:
        _render_schema_tab(result.schema_graph)

    # ---------------- JOIN Graph ----------------
    with tab_join:
        _render_join_tab(result.join_graph)

    # ---------------- Lineage Graph ----------------
    with tab_lineage:
        _render_lineage_tab(result.lineage_graph, result.hyperedges)

    # ---------------- 社区检测 ----------------
    with tab_community:
        _render_community_tab(result)


def _render_schema_tab(schema_graph: Any) -> None:
    """渲染 Schema Graph 标签页。"""
    col1, col2, col3 = st.columns(3)
    col1.metric("节点数", schema_graph.number_of_nodes())
    col2.metric("边数", schema_graph.number_of_edges())
    tables = sum(
        1 for _, d in schema_graph.nodes(data=True)
        if d.get("node_type") is not None and d["node_type"].value == "table"
    )
    col3.metric("表节点", tables)

    with st.expander("过滤与渲染选项"):
        node_type = st.selectbox(
            "节点类型过滤",
            ["全部", "table", "column", "procedure"],
            key="schema_nt",
        )
        max_nodes = st.slider(
            "最大节点数", 20, 300, 100, step=20, key="schema_max"
        )
        height = st.slider("渲染高度", 400, 1000, 600, step=50, key="schema_h")

    filter_nt = None if node_type == "全部" else node_type
    render_graph(
        schema_graph, height=height,
        filter_node_type=filter_nt, max_nodes=max_nodes,
        key="schema_graph_viz",
    )


def _render_join_tab(join_graph: Any) -> None:
    """渲染 JOIN Graph 标签页。"""
    col1, col2 = st.columns(2)
    col1.metric("表节点数", join_graph.number_of_nodes())
    col2.metric("JOIN 边数", join_graph.number_of_edges())

    if join_graph.number_of_edges() == 0:
        st.info("JOIN 图为空（无 FK 与推断 JOIN 边）")
        return

    height = st.slider(
        "渲染高度", 400, 900, 500, step=50, key="join_h"
    )
    render_join_graph(join_graph, height=height)

    st.divider()
    st.subheader("JOIN 条件列表")
    cond_data = []
    for u, v, data in join_graph.edges(data=True):
        cond_data.append({
            "表 A": _to_table_name(u),
            "表 B": _to_table_name(v),
            "JOIN 条件": data.get("join_condition", ""),
            "权重": round(data.get("weight", 1.0), 3),
            "条件数": len(data.get("conditions", [])),
        })
    st.dataframe(cond_data, use_container_width=True)


def _render_lineage_tab(lineage_graph: Any, hyperedges: list) -> None:
    """渲染 Lineage Graph 标签页。"""
    col1, col2, col3 = st.columns(3)
    col1.metric("节点数", lineage_graph.number_of_nodes())
    col2.metric("边数", lineage_graph.number_of_edges())
    col3.metric("超边（过程）", len(hyperedges))

    height = st.slider(
        "渲染高度", 400, 900, 500, step=50, key="lineage_h"
    )
    render_graph(
        lineage_graph, height=height, max_nodes=100, key="lineage_graph_viz"
    )

    st.divider()
    st.subheader("血缘超边列表")
    if not hyperedges:
        st.info("无血缘超边")
        return
    hyper_data = [
        {
            "过程": h.procedure_name,
            "输入表": ", ".join(h.source_tables) or "无",
            "输出表": ", ".join(h.target_tables) or "无",
            "描述": h.properties.get("description", ""),
        }
        for h in hyperedges
    ]
    st.dataframe(hyper_data, use_container_width=True)

    # 上下游查询
    st.divider()
    st.subheader("上下游查询")
    table_names = [
        _to_table_name(n)
        for n, d in lineage_graph.nodes(data=True)
        if d.get("node_type") is not None and d["node_type"].value == "table"
    ]
    if table_names:
        sel = st.selectbox("选择表", table_names, key="lineage_table")
        if sel:
            from fabgraph.graph.lineage_graph import (
                get_upstream_tables, get_downstream_tables,
            )
            up = get_upstream_tables(lineage_graph, sel)
            down = get_downstream_tables(lineage_graph, sel)
            c1, c2 = st.columns(2)
            with c1:
                st.caption("上游表")
                st.write(up if up else "无")
            with c2:
                st.caption("下游表")
                st.write(down if down else "无")


def _render_community_tab(result: Any) -> None:
    """渲染社区检测标签页。"""
    from fabgraph.graph.graph_algorithms import (
        detect_communities, list_communities,
    )
    from fabgraph.graph.graph_utils import (
        to_join_graph, project_lineage_to_undirected,
    )

    c1, c2 = st.columns(2)
    graph_kind = c1.selectbox(
        "图谱选择", ["schema (JOIN)", "lineage"], key="comm_graph"
    )
    method = c2.selectbox(
        "算法", ["auto", "louvain", "girvan_newman"], key="comm_method"
    )

    if graph_kind.startswith("schema"):
        ug = to_join_graph(result.schema_graph)
    else:
        ug = project_lineage_to_undirected(result.lineage_graph)

    if ug.number_of_nodes() == 0:
        st.info("图为空")
        return

    partition = detect_communities(ug, method=method)
    grouped = list_communities(partition)

    m1, m2 = st.columns(2)
    m1.metric("节点数", len(partition))
    m2.metric("社区数", len(grouped))

    # 社区列表
    st.subheader("社区成员")
    for cid in sorted(grouped.keys()):
        members = grouped[cid]
        with st.expander(f"社区 #{cid}（{len(members)} 个表）"):
            st.write([_to_table_name(m) for m in members])

    # 渲染社区图（节点按社区着色）
    if st.checkbox("渲染社区图", value=True, key="comm_render"):
        _render_colored_community(ug, partition)


def _render_colored_community(graph: Any, partition: dict) -> None:
    """渲染按社区着色的图谱。"""
    from pyvis.network import Network
    import streamlit as st

    if graph.number_of_nodes() == 0:
        st.info("图谱为空")
        return

    palette = [
        "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
        "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
        "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000",
    ]
    net = Network(
        height="600px", width="100%", directed=False, notebook=False,
        bgcolor="#1a1a2e", font_color="white",
    )
    for nid in graph.nodes():
        cid = partition.get(nid, 0)
        color = palette[cid % len(palette)]
        name = _to_table_name(nid)
        net.add_node(nid, label=name, color=color, size=25, title=f"社区 #{cid}")
    for u, v, data in graph.edges(data=True):
        net.add_edge(u, v, width=2, title=data.get("join_condition", ""))
    net.set_options(
        '{"physics": {"barnesHut": {"gravitationalConstant": -2000, "springLength": 180}}}'
    )
    try:
        html = net.generate_html(notebook=False)
        st.components.v1.html(html, height=620)
    except Exception as e:
        st.error(f"渲染失败: {e}")


def _to_table_name(node_id: str) -> str:
    """节点 id 转纯表名。"""
    prefix = "table:"
    if node_id.startswith(prefix):
        return node_id[len(prefix):]
    return node_id

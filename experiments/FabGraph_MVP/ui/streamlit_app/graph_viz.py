"""图谱可视化组件（pyvis）。

将 NetworkX 图谱转为 pyvis 交互式 HTML，嵌入 Streamlit。
对应ResNet注意力可视化：直观展示节点间语义连接。
"""
from __future__ import annotations

import streamlit as st
import networkx as nx
from pyvis.network import Network

from fabgraph.models.graph import EdgeType, NodeType

# 节点颜色映射
_NODE_COLORS = {
    NodeType.TABLE: "#4CAF50",       # 绿色
    NodeType.COLUMN: "#2196F3",      # 蓝色
    NodeType.PROCEDURE: "#FF9800",   # 橙色
}

# 边颜色映射
_EDGE_COLORS = {
    EdgeType.HAS_COLUMN: "#9E9E9E",     # 灰色
    EdgeType.FOREIGN_KEY: "#F44336",    # 红色
    EdgeType.JOIN_INFERRED: "#9C27B0",  # 紫色
    EdgeType.READS: "#00BCD4",          # 青色
    EdgeType.WRITES: "#FF5722",         # 深橙
    EdgeType.LINEAGE: "#4CAF50",        # 绿色
}


def render_graph(
    graph: nx.Graph,
    height: int = 600,
    filter_node_type: str | None = None,
    max_nodes: int = 100,
    key: str = "graph",
) -> None:
    """渲染 NetworkX 图谱为 pyvis 交互式 HTML。

    Args:
        graph: NetworkX 图（MultiDiGraph 或 Graph）。
        height: 渲染高度（像素）。
        filter_node_type: 仅显示指定类型节点（table/column/procedure）。
        max_nodes: 最大节点数（超出则截断）。
        key: Streamlit 组件 key。
    """
    if graph.number_of_nodes() == 0:
        st.info("图谱为空")
        return

    # 截断大图
    nodes_to_show = list(graph.nodes)[:max_nodes]
    subgraph = graph.subgraph(nodes_to_show)

    net = Network(
        height=f"{height}px",
        width="100%",
        directed=graph.is_directed(),
        notebook=False,
        bgcolor="#1a1a2e",
        font_color="white",
    )

    # 添加节点
    for nid in subgraph.nodes():
        data = graph.nodes[nid]
        nt = data.get("node_type")
        if filter_node_type and nt and nt.value != filter_node_type:
            continue
        color = _NODE_COLORS.get(nt, "#607D8B")
        label = data.get("name", nid)
        # 截断长标签
        if len(label) > 30:
            label = label[:27] + "..."
        title = data.get("description", "") or label
        net.add_node(
            nid, label=label, color=color, title=title,
            size=25 if nt == NodeType.TABLE else 15,
        )

    # 添加边
    for u, v, data in subgraph.edges(data=True):
        et = data.get("edge_type")
        color = _EDGE_COLORS.get(et, "#757575")
        label = et.value if et else ""
        net.add_edge(u, v, color=color, title=label, width=2)

    # 物理布局
    net.set_options('{"physics": {"barnesHut": {" gravitationalConstant": -3000, "springLength": 150}}}')

    # 生成 HTML 并嵌入
    try:
        html = net.generate_html(notebook=False)
        st.components.v1.html(html, height=height + 20)
    except Exception as e:
        st.error(f"图谱渲染失败: {e}")


def render_join_graph(
    join_graph: nx.Graph,
    height: int = 500,
) -> None:
    """渲染表级 JOIN 图（无向图，节点为表）。"""
    if join_graph.number_of_nodes() == 0:
        st.info("JOIN 图为空")
        return

    net = Network(
        height=f"{height}px", width="100%",
        directed=False, notebook=False,
        bgcolor="#1a1a2e", font_color="white",
    )

    for nid in join_graph.nodes():
        data = join_graph.nodes[nid]
        name = data.get("name", nid)
        net.add_node(nid, label=name, color="#4CAF50", size=30,
                     title=data.get("description", name))

    for u, v, data in join_graph.edges(data=True):
        condition = data.get("join_condition", "")
        weight = data.get("weight", 1.0)
        net.add_edge(u, v, title=condition, width=3 / (1 + weight),
                     color="#FF9800")

    net.set_options('{"physics": {"barnesHut": {"gravitationalConstant": -2000, "springLength": 200}}}')
    try:
        html = net.generate_html(notebook=False)
        st.components.v1.html(html, height=height + 20)
    except Exception as e:
        st.error(f"JOIN 图渲染失败: {e}")

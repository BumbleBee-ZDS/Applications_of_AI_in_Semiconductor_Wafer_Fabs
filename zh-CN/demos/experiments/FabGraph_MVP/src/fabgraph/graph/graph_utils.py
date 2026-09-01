"""图谱通用工具：节点 id 构造/解析、投影与节点模型转换。

这些函数被 schema_graph / lineage_graph / service 共用，
集中在此避免循环依赖与重复定义。

对应ResNet共享卷积核：跨层复用的基础算子。
"""
from __future__ import annotations

import networkx as nx

from fabgraph.models.graph import EdgeType, GraphNode, NodeType
from fabgraph.utils.exceptions import GraphError

# 节点 id 前缀
_TABLE_PREFIX = "table:"
_COLUMN_PREFIX = "column:"
_PROCEDURE_PREFIX = "procedure:"


def table_node_id(table_name: str) -> str:
    """生成 table 节点 id。"""
    return f"{_TABLE_PREFIX}{table_name}"


def column_node_id(table_name: str, column_name: str) -> str:
    """生成 column 节点 id。"""
    return f"{_COLUMN_PREFIX}{table_name}.{column_name}"


def procedure_node_id(procedure_name: str) -> str:
    """生成 procedure 节点 id。"""
    return f"{_PROCEDURE_PREFIX}{procedure_name}"


def parse_node_id(node_id: str) -> tuple[NodeType, str]:
    """解析节点 id 为 (类型, 名称)。

    Raises:
        GraphError: 无法识别的 id 前缀。
    """
    if node_id.startswith(_TABLE_PREFIX):
        return NodeType.TABLE, node_id[len(_TABLE_PREFIX):]
    if node_id.startswith(_COLUMN_PREFIX):
        return NodeType.COLUMN, node_id[len(_COLUMN_PREFIX):]
    if node_id.startswith(_PROCEDURE_PREFIX):
        return NodeType.PROCEDURE, node_id[len(_PROCEDURE_PREFIX):]
    raise GraphError(f"无法识别的节点 id: {node_id}")


def to_graph_node(node_id: str, graph: nx.MultiDiGraph) -> GraphNode:
    """将 NetworkX 节点转换为 :class:`GraphNode` 模型。"""
    node_type, name = parse_node_id(node_id)
    data = graph.nodes[node_id]
    props = {k: v for k, v in data.items() if k != "node_type" and k != "name"}
    return GraphNode(node_id=node_id, node_type=node_type, name=name, properties=props)


def find_table_of_column(
    schema_graph: nx.MultiDiGraph, column_node: str
) -> str | None:
    """从 column 节点回溯所属 table 节点（通过 has_column 反向边）。"""
    for pred in schema_graph.predecessors(column_node):
        data = schema_graph.nodes[pred]
        if data.get("node_type") == NodeType.TABLE:
            return pred
    return None


def to_join_graph(schema_graph: nx.MultiDiGraph) -> nx.Graph:
    """将 Schema Graph 投影为表级无向 JOIN 图。

    保留 ``foreign_key`` 与 ``join_inferred`` 边，聚合为 table-table 边，
    权重取最小（最短路径偏好 FK 与高频 JOIN）。

    Args:
        schema_graph: Schema Graph。

    Returns:
        :class:`networkx.Graph` 表级无向图，边属性含 weight/join_condition。
    """
    join_graph = nx.Graph()
    for u, v, data in schema_graph.edges(data=True):
        edge_type = data.get("edge_type")
        if edge_type not in (EdgeType.FOREIGN_KEY, EdgeType.JOIN_INFERRED):
            continue
        t_u = find_table_of_column(schema_graph, u)
        t_v = find_table_of_column(schema_graph, v)
        if not t_u or not t_v or t_u == t_v:
            continue
        col_u = schema_graph.nodes[u].get("name", u)
        col_v = schema_graph.nodes[v].get("name", v)
        condition = (
            f"{schema_graph.nodes[t_u]['name']}.{col_u} = "
            f"{schema_graph.nodes[t_v]['name']}.{col_v}"
        )
        weight = data.get("weight", 1.0)
        if join_graph.has_edge(t_u, t_v):
            existing = join_graph[t_u][t_v]
            if weight < existing.get("weight", 1.0):
                existing["weight"] = weight
                existing["join_condition"] = condition
            existing["conditions"] = existing.get("conditions", []) + [condition]
        else:
            join_graph.add_edge(
                t_u, t_v, weight=weight, join_condition=condition,
                conditions=[condition],
            )
    return join_graph


def project_lineage_to_undirected(lineage_graph: nx.MultiDiGraph) -> nx.Graph:
    """将 Lineage Graph 投影为无向图用于社区检测。

    保留 ``lineage`` 与 ``reads/writes`` 关系（忽略方向），
    边权重聚合为出现次数。

    Args:
        lineage_graph: Lineage Graph。

    Returns:
        :class:`networkx.Graph` 无向投影。
    """
    undirected = nx.Graph()
    for node, data in lineage_graph.nodes(data=True):
        undirected.add_node(node, **data)
    for u, v, data in lineage_graph.edges(data=True):
        edge_type = data.get("edge_type")
        if edge_type is None:
            continue
        if undirected.has_edge(u, v):
            undirected[u][v]["weight"] += 1.0
        else:
            undirected.add_edge(u, v, weight=1.0, edge_type=edge_type)
    return undirected

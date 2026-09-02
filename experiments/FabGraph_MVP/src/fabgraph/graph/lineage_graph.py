"""Lineage Graph 构建。

Lineage Graph 描述数据血缘：过程读/写哪些表，表间数据流向。

节点：
- table 节点 (id: ``table:TABLE_NAME``)
- procedure 节点 (id: ``procedure:PROC_NAME``)

边（:class:`networkx.MultiDiGraph`）：
- ``reads``: procedure -> table
- ``writes``: procedure -> table
- ``lineage``: table -> table（由过程推导：每个 input_table -> 每个 output_table）

超边：每个 procedure 作为 :class:`HyperEdge`，连接其 input/output 表集合。
超边存于图属性 ``hyperedges``（dict[edge_id, HyperEdge]），
使 NetworkX 图本身仍为简单有向图，便于路径/社区算法。

对应ResNet残差连接：过程节点把多表语义聚合后写入下游表，
避免逐表特征传递时血缘信号衰减。
"""
from __future__ import annotations

import logging
from typing import Iterable

import networkx as nx

from fabgraph.models.graph import EdgeType, HyperEdge, NodeType
from fabgraph.models.schema import Procedure, Table
from fabgraph.utils.exceptions import GraphError

from .graph_utils import procedure_node_id, table_node_id

logger = logging.getLogger(__name__)

# 图属性键
HYPEREDGES_ATTR = "hyperedges"


class LineageGraphBuilder:
    """Lineage Graph 构建器。"""

    def build(
        self,
        tables: Iterable[Table],
        procedures: Iterable[Procedure],
    ) -> nx.MultiDiGraph:
        """构建 Lineage Graph。

        Args:
            tables: 表元数据（仅取表名作为节点）。
            procedures: 存储过程元数据（含 input/output 表）。

        Returns:
            :class:`networkx.MultiDiGraph` Lineage Graph，
            其 ``graph.hyperedges`` 属性为超边字典。
        """
        graph = nx.MultiDiGraph()
        graph.graph[HYPEREDGES_ATTR] = {}
        table_list = list(tables)
        proc_list = list(procedures)
        valid_table_names = {t.table_name for t in table_list}

        for table in table_list:
            self._add_table(graph, table)
        for proc in proc_list:
            self._add_procedure_and_hyperedge(graph, proc, valid_table_names)
        # 由过程 reads/writes 推导 table -> table lineage 边
        self._add_lineage_edges(graph, proc_list, valid_table_names)

        logger.info(
            "Lineage Graph 构建完成: 节点=%d 边=%d 超边=%d",
            graph.number_of_nodes(),
            graph.number_of_edges(),
            len(graph.graph[HYPEREDGES_ATTR]),
        )
        return graph

    def _add_table(self, graph: nx.MultiDiGraph, table: Table) -> None:
        """添加 table 节点。"""
        graph.add_node(
            table_node_id(table.table_name),
            node_type=NodeType.TABLE,
            name=table.table_name,
            description=table.description,
            row_count=table.row_count,
            tags=list(table.tags),
        )

    def _add_procedure_and_hyperedge(
        self,
        graph: nx.MultiDiGraph,
        proc: Procedure,
        valid_table_names: set[str],
    ) -> None:
        """添加 procedure 节点 + reads/writes 边 + 超边。"""
        p_node = procedure_node_id(proc.procedure_name)
        graph.add_node(
            p_node,
            node_type=NodeType.PROCEDURE,
            name=proc.procedure_name,
            description=proc.description,
            schema_name=proc.schema_name,
        )
        for t in proc.input_tables:
            if t not in valid_table_names:
                logger.warning("过程 %s 读取未注册的表 %s，已跳过", proc.procedure_name, t)
                continue
            graph.add_edge(
                p_node, table_node_id(t),
                edge_type=EdgeType.READS, weight=1.0,
            )
        for t in proc.output_tables:
            if t not in valid_table_names:
                logger.warning("过程 %s 写入未注册的表 %s，已跳过", proc.procedure_name, t)
                continue
            graph.add_edge(
                p_node, table_node_id(t),
                edge_type=EdgeType.WRITES, weight=1.0,
            )
        # 超边：仅当至少有一个输入或输出表
        if proc.input_tables or proc.output_tables:
            hyper = HyperEdge(
                edge_id=f"hyper:{proc.procedure_name}",
                procedure_name=proc.procedure_name,
                source_tables=list(proc.input_tables),
                target_tables=list(proc.output_tables),
                properties={"description": proc.description},
            )
            graph.graph[HYPEREDGES_ATTR][hyper.edge_id] = hyper

    def _add_lineage_edges(
        self,
        graph: nx.MultiDiGraph,
        procedures: list[Procedure],
        valid_table_names: set[str],
    ) -> None:
        """由过程推导 table -> table 的 lineage 边。

        对每个过程：每个 input_table -> 每个 output_table 建立一条 lineage 边。
        若 input == output（自更新）则跳过，避免自环。
        """
        added = 0
        for proc in procedures:
            inputs = [t for t in proc.input_tables if t in valid_table_names]
            outputs = [t for t in proc.output_tables if t in valid_table_names]
            for src in inputs:
                for dst in outputs:
                    if src == dst:
                        continue
                    graph.add_edge(
                        table_node_id(src), table_node_id(dst),
                        edge_type=EdgeType.LINEAGE,
                        weight=1.0,
                        procedure=proc.procedure_name,
                    )
                    added += 1
        logger.debug("lineage 边: %d", added)


def get_hyperedges(graph: nx.MultiDiGraph) -> dict[str, HyperEdge]:
    """获取 Lineage Graph 中全部超边。

    Args:
        graph: Lineage Graph。

    Returns:
        edge_id -> HyperEdge 字典。

    Raises:
        GraphError: 图缺少超边属性（非 Lineage Graph）。
    """
    if HYPEREDGES_ATTR not in graph.graph:
        raise GraphError("图中缺少 hyperedges 属性，可能不是 Lineage Graph")
    return dict(graph.graph[HYPEREDGES_ATTR])


def get_upstream_tables(graph: nx.MultiDiGraph, table_name: str) -> list[str]:
    """获取指定表的全部上游表（递归沿 lineage 反向）。

    Args:
        graph: Lineage Graph。
        table_name: 起始表名。

    Returns:
        上游表名列表（去重，不含自身）。
    """
    start = table_node_id(table_name)
    if start not in graph:
        return []
    visited: set[str] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        for pred, _, data in graph.in_edges(node, data=True):
            if data.get("edge_type") != EdgeType.LINEAGE:
                continue
            if pred in visited or pred == start:
                continue
            visited.add(pred)
            stack.append(pred)
    return [parse_table_name(n) for n in visited]


def get_downstream_tables(graph: nx.MultiDiGraph, table_name: str) -> list[str]:
    """获取指定表的全部下游表（递归沿 lineage 正向）。"""
    start = table_node_id(table_name)
    if start not in graph:
        return []
    visited: set[str] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        for _, succ, data in graph.out_edges(node, data=True):
            if data.get("edge_type") != EdgeType.LINEAGE:
                continue
            if succ in visited or succ == start:
                continue
            visited.add(succ)
            stack.append(succ)
    return [parse_table_name(n) for n in visited]


def parse_table_name(node_id: str) -> str:
    """从 table 节点 id 提取表名。"""
    prefix = "table:"
    if node_id.startswith(prefix):
        return node_id[len(prefix):]
    return node_id

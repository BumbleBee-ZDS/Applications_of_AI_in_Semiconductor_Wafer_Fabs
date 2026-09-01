"""Schema Graph 构建。

Schema Graph 节点：
- table 节点 (id: ``table:TABLE_NAME``)
- column 节点 (id: ``column:TABLE_NAME.COLUMN_NAME``)
- procedure 节点 (id: ``procedure:PROC_NAME``)（独立实体，关系在 Lineage Graph）

Schema Graph 边：
- ``has_column``: table -> column
- ``foreign_key``: column -> column（FK 字段引用 PK 字段）
- ``join_inferred``: column -> column（双向，源自 SQL 历史的 JOIN 推断）

使用 :class:`networkx.MultiDiGraph` 以容纳多种边类型。
对应ResNet跨层连接：表节点间通过共享字段语义建立"短路"路径。
"""
from __future__ import annotations

import logging
from typing import Iterable

import networkx as nx

from fabgraph.models.graph import EdgeType, NodeType
from fabgraph.models.schema import (
    Column,
    ColumnSemanticType,
    Procedure,
    SemanticHint,
    Table,
)

from .graph_utils import (
    column_node_id,
    procedure_node_id,
    table_node_id,
)

logger = logging.getLogger(__name__)

# column 节点 id 前缀（_resolve_column_node 用）
_COLUMN_PREFIX = "column:"


class SchemaGraphBuilder:
    """Schema Graph 构建器。

    对应ResNet前向传播：逐层注入表/字段/FK/JOIN 语义。
    """

    def build(
        self,
        tables: Iterable[Table],
        procedures: Iterable[Procedure] | None = None,
        semantic_hints: Iterable[SemanticHint] | None = None,
    ) -> nx.MultiDiGraph:
        """构建 Schema Graph。

        Args:
            tables: 表元数据（含字段）。
            procedures: 存储过程元数据（仅作实体节点加入）。
            semantic_hints: SQL 推断的语义提示（用于 join_inferred 边）。

        Returns:
            :class:`networkx.MultiDiGraph` Schema Graph。
        """
        graph = nx.MultiDiGraph()
        table_pk_map: dict[str, str | None] = {}
        table_list: list[Table] = list(tables)
        for table in table_list:
            self._add_table(graph, table, table_pk_map)
        # FK 边需要全表 PK 信息，故分两步
        self._add_foreign_key_edges(graph, table_list, table_pk_map)
        if procedures:
            for proc in procedures:
                self._add_procedure(graph, proc)
        if semantic_hints:
            self._add_join_inferred_edges(graph, list(semantic_hints))
        logger.info(
            "Schema Graph 构建完成: 节点=%d 边=%d (表=%d)",
            graph.number_of_nodes(),
            graph.number_of_edges(),
            len(table_list),
        )
        return graph

    def _add_table(
        self,
        graph: nx.MultiDiGraph,
        table: Table,
        table_pk_map: dict[str, str | None],
    ) -> None:
        """添加表节点、字段节点及 has_column 边。"""
        t_node_id = table_node_id(table.table_name)
        graph.add_node(
            t_node_id,
            node_type=NodeType.TABLE,
            name=table.table_name,
            description=table.description,
            row_count=table.row_count,
            tags=list(table.tags),
        )
        pk_column: str | None = None
        for col in table.columns:
            c_node_id = column_node_id(table.table_name, col.column_name)
            graph.add_node(
                c_node_id,
                node_type=NodeType.COLUMN,
                name=col.column_name,
                table_name=table.table_name,
                data_type=col.data_type,
                nullable=col.nullable,
                position=col.position,
                semantic_type=col.semantic_type.value,
                semantic_label=col.semantic_label,
                description=col.description,
                confidence=col.confidence,
                aliases=list(col.aliases),
            )
            graph.add_edge(
                t_node_id,
                c_node_id,
                edge_type=EdgeType.HAS_COLUMN,
                weight=1.0,
            )
            if col.semantic_type == ColumnSemanticType.PRIMARY_KEY and not pk_column:
                pk_column = col.column_name
        table_pk_map[table.table_name] = pk_column

    def _add_foreign_key_edges(
        self,
        graph: nx.MultiDiGraph,
        tables: list[Table],
        table_pk_map: dict[str, str | None],
    ) -> None:
        """添加 foreign_key 边。

        双重启发式：
        1. **PK 名称匹配（优先）**：FK 字段名 == 某表的 PK 字段名，
           则认为引用该表（如 WFR_ID 在 LOT_HISTORY 是 FK，
           WAFER_RESULT 的 PK 也是 WFR_ID）。
        2. **命名前缀匹配（兜底）**：FK 字段形如 ``<TABLE>_ID`` /
           ``<TABLE>_CD`` / ``<TABLE>_KEY``，且表名存在。
        """
        table_names = {t.table_name.upper() for t in tables}
        # PK 列名 -> 所属表名（同名 PK 仅取首张）
        pk_name_to_table: dict[str, str] = {}
        for tname, pk in table_pk_map.items():
            if pk:
                pk_name_to_table.setdefault(pk.upper(), tname)
        added = 0
        for table in tables:
            for col in table.columns:
                if col.semantic_type != ColumnSemanticType.FOREIGN_KEY:
                    continue
                ref_table = self._resolve_fk_target(
                    col.column_name, table.table_name,
                    pk_name_to_table, table_names,
                )
                if not ref_table:
                    continue
                ref_pk = table_pk_map.get(ref_table)
                if not ref_pk:
                    continue
                graph.add_edge(
                    column_node_id(table.table_name, col.column_name),
                    column_node_id(ref_table, ref_pk),
                    edge_type=EdgeType.FOREIGN_KEY,
                    weight=0.5,  # FK 边权较小，便于 JOIN 路径偏好
                    inferred=True,
                )
                added += 1
        logger.debug("foreign_key 边: %d", added)

    @staticmethod
    def _resolve_fk_target(
        column_name: str,
        owner_table: str,
        pk_name_to_table: dict[str, str],
        table_names: set[str],
    ) -> str | None:
        """解析 FK 字段引用的目标表。

        Args:
            column_name: FK 字段名。
            owner_table: FK 所属表（避免自引用）。
            pk_name_to_table: PK 列名 -> 表名 映射。
            table_names: 全部表名集合（大写）。

        Returns:
            目标表名，未匹配返回 None。
        """
        upper = column_name.upper()
        # 1) PK 名称匹配
        if upper in pk_name_to_table:
            candidate = pk_name_to_table[upper]
            if candidate != owner_table:
                return candidate
        # 2) 命名前缀匹配
        return SchemaGraphBuilder._infer_ref_table(upper, table_names)

    @staticmethod
    def _infer_ref_table(column_name: str, table_names: set[str]) -> str | None:
        """根据字段名推断引用表。

        Args:
            column_name: FK 字段名。
            table_names: 候选表名集合（大写）。

        Returns:
            匹配的表名，未匹配返回 None。
        """
        upper = column_name.upper()
        # 优先精确前缀匹配：LOT_ID -> LOT, WFR_ID -> WFR (需表名也短形)
        # 通用的 <TABLE>_ID / <TABLE>_CD 模式
        for suffix in ("_ID", "_CD", "_KEY"):
            if upper.endswith(suffix):
                prefix = upper[: -len(suffix)]
                # 1) prefix 直接命中
                if prefix in table_names:
                    return prefix
                # 2) prefix + S 命中（单复数）
                if f"{prefix}S" in table_names:
                    return f"{prefix}S"
                # 3) prefix + HISTORY 命中
                if f"{prefix}_HISTORY" in table_names:
                    return f"{prefix}_HISTORY"
        return None

    def _add_procedure(self, graph: nx.MultiDiGraph, proc: Procedure) -> None:
        """添加 procedure 节点（schema 图中不与表连边，关系归 Lineage Graph）。"""
        p_node_id = procedure_node_id(proc.procedure_name)
        graph.add_node(
            p_node_id,
            node_type=NodeType.PROCEDURE,
            name=proc.procedure_name,
            description=proc.description,
            schema_name=proc.schema_name,
        )

    def _add_join_inferred_edges(
        self,
        graph: nx.MultiDiGraph,
        hints: list[SemanticHint],
    ) -> None:
        """根据语义提示添加 join_inferred 边。

        hint_type == 'join_key' 的提示用于在两个字段间建立双向 JOIN 边。
        本地字段由 ``hint.table_name.column_name`` 构成，
        远端字段为 ``hint.hint_value``（应为 ``TABLE.COLUMN`` 形式）。
        weight = 1 / (1 + frequency)。
        """
        added = 0
        # 同 (local, remote) 对聚合频次
        freq: dict[tuple[str, str], int] = {}
        for h in hints:
            if h.hint_type != "join_key" or not h.hint_value:
                continue
            local_ref = f"{h.table_name}.{h.column_name}"
            key = (local_ref, h.hint_value)
            freq[key] = freq.get(key, 0) + 1
        for (left, right), count in freq.items():
            left_node = self._resolve_column_node(graph, left)
            right_node = self._resolve_column_node(graph, right)
            if not left_node or not right_node:
                continue
            weight = 1.0 / (1.0 + count)
            graph.add_edge(
                left_node, right_node,
                edge_type=EdgeType.JOIN_INFERRED, weight=weight, frequency=count,
            )
            graph.add_edge(
                right_node, left_node,
                edge_type=EdgeType.JOIN_INFERRED, weight=weight, frequency=count,
            )
            added += 2
        logger.debug("join_inferred 边: %d", added)

    @staticmethod
    def _resolve_column_node(graph: nx.MultiDiGraph, ref: str) -> str | None:
        """将 ``TABLE.COLUMN`` 形式解析为 column 节点 id。"""
        node_id = f"{_COLUMN_PREFIX}{ref}"
        if node_id in graph:
            return node_id
        # 容忍大小写差异
        upper = ref.upper()
        for n in graph.nodes:
            if n.startswith(_COLUMN_PREFIX) and n[len(_COLUMN_PREFIX):].upper() == upper:
                return n
        return None

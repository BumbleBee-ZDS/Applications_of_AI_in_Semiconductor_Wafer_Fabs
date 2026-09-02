"""图谱构建服务。

编排流程：
1. 从 :class:`MetadataRepository` 加载元数据（tables/procedures）
2. 调用 :class:`SchemaGraphBuilder` 构建 Schema Graph
3. 调用 :class:`LineageGraphBuilder` 构建 Lineage Graph
4. 通过 :class:`GraphRepository` 持久化两个图谱快照

依赖注入：所有仓储通过构造函数注入，便于测试 mock。
对应ResNet训练循环：数据 -> 前向传播 -> 权重持久化。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

import networkx as nx

from fabgraph.config import Settings, get_settings
from fabgraph.graph.lineage_graph import LineageGraphBuilder
from fabgraph.graph.schema_graph import SchemaGraphBuilder
from fabgraph.graph.graph_utils import to_join_graph
from fabgraph.models.graph import HyperEdge
from fabgraph.models.schema import Procedure, SemanticHint, Table
from fabgraph.repository.graph_repo import GraphRepository
from fabgraph.repository.metadata_repo import MetadataRepository
from fabgraph.utils.exceptions import GraphError

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """图谱构建结果。

    Attributes:
        schema_graph: Schema Graph。
        lineage_graph: Lineage Graph。
        join_graph: 由 Schema Graph 投影的表级 JOIN 图。
        table_count: 表数量。
        procedure_count: 过程数量。
        hyperedges: Lineage Graph 的超边列表。
    """

    schema_graph: nx.MultiDiGraph
    lineage_graph: nx.MultiDiGraph
    join_graph: nx.Graph
    table_count: int = 0
    procedure_count: int = 0
    hyperedges: list[HyperEdge] = field(default_factory=list)

    def summary(self) -> dict[str, int]:
        """返回构建统计摘要。"""
        return {
            "tables": self.table_count,
            "procedures": self.procedure_count,
            "schema_nodes": self.schema_graph.number_of_nodes(),
            "schema_edges": self.schema_graph.number_of_edges(),
            "lineage_nodes": self.lineage_graph.number_of_nodes(),
            "lineage_edges": self.lineage_graph.number_of_edges(),
            "join_edges": self.join_graph.number_of_edges(),
            "hyperedges": len(self.hyperedges),
        }


class GraphBuilderService:
    """图谱构建编排服务。

    依赖 :class:`MetadataRepository` 与 :class:`GraphRepository`，
    自身不直接访问数据库或文件系统。
    """

    def __init__(
        self,
        metadata_repo: MetadataRepository | None = None,
        graph_repo: GraphRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        """初始化服务。

        Args:
            metadata_repo: 元数据仓储，默认按配置创建。
            graph_repo: 图谱仓储，默认按配置创建。
            settings: 配置对象，默认使用全局单例。
        """
        self._settings = settings or get_settings()
        self.metadata_repo = metadata_repo or MetadataRepository(self._settings)
        self.graph_repo = graph_repo or GraphRepository(self._settings)
        self._schema_builder = SchemaGraphBuilder()
        self._lineage_builder = LineageGraphBuilder()

    def build_all(
        self,
        semantic_hints: Iterable[SemanticHint] | None = None,
        persist: bool = True,
    ) -> BuildResult:
        """构建并（可选）持久化 Schema Graph 与 Lineage Graph。

        Args:
            semantic_hints: SQL 推断的语义提示（注入 join_inferred 边）。
            persist: 是否持久化到 pickle。

        Returns:
            :class:`BuildResult` 构建结果。

        Raises:
            GraphError: 构建失败。
        """
        tables = self.metadata_repo.get_tables()
        procedures = self.metadata_repo.get_procedures()
        if not tables:
            raise GraphError("元数据为空，请先执行 load_from_json")

        logger.info(
            "开始构建图谱: 表=%d 过程=%d hints=%s",
            len(tables), len(procedures),
            len(list(semantic_hints)) if semantic_hints else 0,
        )
        schema_graph = self._schema_builder.build(
            tables, procedures, semantic_hints
        )
        lineage_graph = self._lineage_builder.build(tables, procedures)
        join_graph = to_join_graph(schema_graph)
        hyperedges = self._collect_hyperedges(lineage_graph)

        result = BuildResult(
            schema_graph=schema_graph,
            lineage_graph=lineage_graph,
            join_graph=join_graph,
            table_count=len(tables),
            procedure_count=len(procedures),
            hyperedges=hyperedges,
        )
        logger.info("图谱构建完成: %s", result.summary())
        if persist:
            self._persist(result)
        return result

    def load_or_build(self, persist: bool = True) -> BuildResult:
        """优先加载已持久化的图谱快照，否则构建。

        Args:
            persist: 构建后是否持久化。

        Returns:
            :class:`BuildResult`。
        """
        existing = self.graph_repo.exists()
        if existing["schema_graph"] and existing["lineage_graph"]:
            try:
                schema_graph = self.graph_repo.load_schema_graph()
                lineage_graph = self.graph_repo.load_lineage_graph()
                if schema_graph is not None and lineage_graph is not None:
                    return self._assemble_from_loaded(
                        schema_graph, lineage_graph
                    )
            except GraphError as e:
                logger.warning("加载快照失败，回退到重新构建: %s", e)

        return self.build_all(persist=persist)

    def _assemble_from_loaded(
        self,
        schema_graph: nx.MultiDiGraph,
        lineage_graph: nx.MultiDiGraph,
    ) -> BuildResult:
        """从已加载的两个图组装 :class:`BuildResult`。"""
        join_graph = to_join_graph(schema_graph)
        hyperedges = self._collect_hyperedges(lineage_graph)
        table_count = sum(
            1 for _, d in schema_graph.nodes(data=True)
            if d.get("node_type") is not None and d["node_type"].value == "table"
        ) if schema_graph.number_of_nodes() else 0
        proc_count = sum(
            1 for _, d in lineage_graph.nodes(data=True)
            if d.get("node_type") is not None and d["node_type"].value == "procedure"
        ) if lineage_graph.number_of_nodes() else 0
        result = BuildResult(
            schema_graph=schema_graph,
            lineage_graph=lineage_graph,
            join_graph=join_graph,
            table_count=table_count,
            procedure_count=proc_count,
            hyperedges=hyperedges,
        )
        logger.info("已加载图谱快照: %s", result.summary())
        return result

    @staticmethod
    def _collect_hyperedges(
        lineage_graph: nx.MultiDiGraph
    ) -> list[HyperEdge]:
        """从 Lineage Graph 提取超边列表。"""
        hyper_dict = lineage_graph.graph.get("hyperedges", {})
        return list(hyper_dict.values())

    def _persist(self, result: BuildResult) -> None:
        """持久化两个图谱。"""
        self.graph_repo.save_schema_graph(result.schema_graph)
        self.graph_repo.save_lineage_graph(result.lineage_graph)
        logger.info("图谱已持久化")

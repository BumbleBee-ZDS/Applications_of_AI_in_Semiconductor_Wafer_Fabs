"""语义检索服务。

职责：
1. 从元数据构建 :class:`EmbeddingItem` 索引（表/字段/过程）
2. 通过 :class:`VectorRepository` 持久化
3. 对自然语言问题检索 top-k 相关表/字段
4. 借助 Schema Graph 做一跳扩展召回

对应ResNet检索增强：向量近邻 + 图谱邻居共同召回，
避免单纯向量相似度漏召远端但语义相关的字段。
"""
from __future__ import annotations

import logging
from typing import Iterable

import networkx as nx

from fabgraph.config import Settings, get_settings
from fabgraph.graph.graph_utils import (
    column_node_id,
    parse_node_id,
    table_node_id,
)
from fabgraph.models.graph import NodeType
from fabgraph.models.schema import Column, Procedure, Table
from fabgraph.models.semantic import EmbeddingItem, SearchResult
from fabgraph.repository.metadata_repo import MetadataRepository
from fabgraph.repository.vector_repo import VectorRepository
from fabgraph.utils.embeddings import EmbeddingClient
from fabgraph.utils.exceptions import SearchError

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """语义检索服务。

    依赖 :class:`MetadataRepository`、:class:`VectorRepository`、
    :class:`EmbeddingClient`，可通过构造函数注入便于测试。
    """

    def __init__(
        self,
        metadata_repo: MetadataRepository | None = None,
        vector_repo: VectorRepository | None = None,
        embedding_client: EmbeddingClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        """初始化语义检索服务。

        Args:
            metadata_repo: 元数据仓储。
            vector_repo: 向量仓储。
            embedding_client: 嵌入客户端。
            settings: 配置对象。
        """
        self._settings = settings or get_settings()
        self.metadata_repo = metadata_repo or MetadataRepository(self._settings)
        self.vector_repo = vector_repo or VectorRepository(self._settings)
        self.embedding_client = embedding_client or EmbeddingClient(self._settings)
        self._indexed = False
        self._schema_graph: nx.MultiDiGraph | None = None

    def set_schema_graph(self, graph: nx.MultiDiGraph) -> None:
        """注入已构建的 Schema Graph，用于图扩展。

        Args:
            graph: Schema Graph。
        """
        self._schema_graph = graph
        logger.debug("已注入 Schema Graph: 节点=%d", graph.number_of_nodes())

    def index_metadata(self) -> int:
        """从元数据构建向量索引。

        为每张表、每个字段生成 :class:`EmbeddingItem`，
        文本包含名称/描述/别名/语义标签。

        Returns:
            索引项数量。
        """
        tables = self.metadata_repo.get_tables()
        procedures = self.metadata_repo.get_procedures()
        items: list[EmbeddingItem] = []
        for table in tables:
            items.append(self._table_to_embedding(table))
            for col in table.columns:
                items.append(self._column_to_embedding(table, col))
        for proc in procedures:
            items.append(self._procedure_to_embedding(proc))
        # 批量嵌入
        texts = [it.text for it in items]
        vectors = self.embedding_client.embed(texts) if texts else []
        if len(vectors) != len(items):
            raise SearchError(
                f"嵌入数量不匹配: 期望 {len(items)} 实际 {len(vectors)}"
            )
        for it, vec in zip(items, vectors):
            it.vector = vec
        self.vector_repo.upsert(items)
        self.vector_repo.build_index()
        self.vector_repo.save()
        self._indexed = True
        logger.info("向量索引构建完成: %d 项", len(items))
        return len(items)

    def search(
        self,
        question: str,
        top_k: int = 5,
        expand: bool = True,
    ) -> list[SearchResult]:
        """语义检索。

        Args:
            question: 自然语言问题。
            top_k: 返回前 K 条。
            expand: 是否启用一跳图扩展。

        Returns:
            :class:`SearchResult` 列表，按相似度降序。
        """
        if not self._indexed and len(self.vector_repo) == 0:
            self.index_metadata()
        q_vec = self.embedding_client.embed_one(question)
        pairs = self.vector_repo.search(q_vec, top_k=top_k)
        results = [
            self._to_search_result(item, score)
            for item, score in pairs
        ]
        if expand and self._schema_graph:
            results = self._expand_with_graph(results)
        return results

    def search_tables(
        self, question: str, top_k: int = 5, expand: bool = True
    ) -> list[SearchResult]:
        """仅检索表级结果（过滤出 table 节点）。

        字段数量远多于表，故扩大候选池确保表被召回。
        """
        # 扩大候选池：字段数通常 10x 表数
        pool_k = max(top_k * 5, 30)
        results = self.search(question, top_k=pool_k, expand=False)
        tables = [r for r in results if r.node_type == NodeType.TABLE]
        return tables[:top_k]

    # ---------------- 图扩展 ----------------

    def _expand_with_graph(
        self, results: list[SearchResult]
    ) -> list[SearchResult]:
        """对检索结果做一跳图扩展。

        已命中表的同表字段或 FK 关联表获得分数加成。
        """
        assert self._schema_graph is not None
        expanded: list[SearchResult] = list(results)
        existing_ids = {r.item_id for r in results}
        for r in results:
            if r.node_type != NodeType.TABLE:
                continue
            _, table_name = parse_node_id(r.item_id)
            # 同表字段加成
            for succ in self._schema_graph.successors(table_node_id(table_name)):
                if succ in existing_ids:
                    continue
                node_data = self._schema_graph.nodes[succ]
                if node_data.get("node_type") != NodeType.COLUMN:
                    continue
                expanded.append(self._make_expanded_result(succ, r.score * 0.7))
                existing_ids.add(succ)
        # 重新排序
        expanded.sort(key=lambda x: x.score, reverse=True)
        return expanded

    def _make_expanded_result(
        self, node_id: str, score: float
    ) -> SearchResult:
        """从图节点构造扩展结果。"""
        assert self._schema_graph is not None
        data = self._schema_graph.nodes[node_id]
        item = EmbeddingItem(
            item_id=node_id, text=data.get("name", ""),
            vector=[], metadata=dict(data),
        )
        return SearchResult(
            item_id=node_id,
            table_name=data.get("table_name", ""),
            column_name=data.get("name", ""),
            node_type=data.get("node_type", NodeType.COLUMN),
            score=score, item=item, expanded_from="graph",
            metadata=dict(data),
        )

    @staticmethod
    def _to_search_result(item: EmbeddingItem, score: float) -> SearchResult:
        """EmbeddingItem + 分数 -> SearchResult。

        表级结果给予 1.5x 分数加成，避免被大量字段淹没。
        """
        node_type = SemanticSearchService._infer_type(item.item_id)
        # 从 item_id 解析表名/字段名
        table_name = item.metadata.get("table", "")
        column_name = ""
        if node_type == NodeType.COLUMN:
            # item_id 形如 column:TABLE.COLUMN
            parts = item.item_id.split(":", 1)[-1].split(".", 1)
            if len(parts) == 2:
                table_name = table_name or parts[0]
                column_name = parts[1]
        elif node_type == NodeType.TABLE:
            table_name = item.item_id.split(":", 1)[-1]
            score *= 1.5  # 表级加成
        return SearchResult(
            item_id=item.item_id, table_name=table_name,
            column_name=column_name, node_type=node_type,
            score=score, item=item, metadata=item.metadata,
        )

    # ---------------- 嵌入项构造 ----------------

    @staticmethod
    def _table_to_embedding(table: Table) -> EmbeddingItem:
        """表 -> EmbeddingItem。"""
        parts = [table.table_name, table.description]
        if table.tags:
            parts.append(" ".join(table.tags))
        text = " ".join(p for p in parts if p)
        return EmbeddingItem(
            item_id=table_node_id(table.table_name),
            text=text,
            metadata={"type": "table", "row_count": table.row_count},
        )

    @staticmethod
    def _column_to_embedding(table: Table, col: Column) -> EmbeddingItem:
        """字段 -> EmbeddingItem。"""
        parts = [
            table.table_name, col.column_name, col.description,
            col.semantic_label, col.semantic_type.value,
        ]
        if col.aliases:
            parts.append(" ".join(col.aliases))
        text = " ".join(p for p in parts if p)
        return EmbeddingItem(
            item_id=column_node_id(table.table_name, col.column_name),
            text=text,
            metadata={
                "type": "column", "table": table.table_name,
                "data_type": col.data_type,
            },
        )

    @staticmethod
    def _procedure_to_embedding(proc: Procedure) -> EmbeddingItem:
        """过程 -> EmbeddingItem。"""
        text = " ".join([proc.procedure_name, proc.description])
        return EmbeddingItem(
            item_id=f"procedure:{proc.procedure_name}",
            text=text,
            metadata={"type": "procedure"},
        )

    @staticmethod
    def _infer_type(node_id: str) -> NodeType:
        """从节点 id 推断类型。"""
        try:
            t, _ = parse_node_id(node_id)
            return t
        except Exception:
            return NodeType.TABLE

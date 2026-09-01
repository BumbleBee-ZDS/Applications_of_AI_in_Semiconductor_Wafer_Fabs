"""数据模型层 (model)。

聚合 schema / graph / semantic 三类核心模型，
供 repository 与 service 层引用。
对应ResNet第一层：将原始元数据标准化为张量化结构。
"""
from __future__ import annotations

from fabgraph.models.graph import (
    EdgeType,
    GraphEdge,
    GraphNode,
    HyperEdge,
    JoinPath,
    NodeType,
)
from fabgraph.models.schema import (
    Column,
    ColumnSemanticType,
    Procedure,
    SemanticHint,
    Table,
)
from fabgraph.models.semantic import (
    EmbeddingItem,
    NL2SQLRequest,
    NL2SQLResponse,
    SearchResult,
)

__all__ = [
    # schema
    "Column",
    "ColumnSemanticType",
    "Table",
    "Procedure",
    "SemanticHint",
    # graph
    "GraphNode",
    "GraphEdge",
    "NodeType",
    "EdgeType",
    "HyperEdge",
    "JoinPath",
    # semantic
    "EmbeddingItem",
    "SearchResult",
    "NL2SQLRequest",
    "NL2SQLResponse",
]

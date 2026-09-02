"""语义搜索与向量模型。

定义向量索引项、语义搜索结果以及 NL2SQL 请求/响应模型。

对应ResNet输出头：向量检索 + 图谱扩展联合产出
语义候选，再由 NL2SQL 头映射为最终 SQL。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from fabgraph.models.graph import NodeType


class EmbeddingItem(BaseModel):
    """单个向量索引项。

    Attributes:
        item_id: 表/字段唯一 id（如 table:LOT_HISTORY 或 column:LOT_HISTORY.LOT_ID）。
        text: 用于嵌入的文本（表名 + 字段名 + 推断语义）。
        vector: 嵌入向量。
        metadata: 附加元数据（表名、字段名、语义标签等）。
    """

    item_id: str
    text: str
    vector: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """语义搜索单条结果。

    Attributes:
        item_id: 命中项 id。
        table_name: 所属表。
        column_name: 所属字段（表级结果为空）。
        node_type: 节点类型（table/column/procedure）。
        score: 相似度分数 [0,1]。
        expanded_from: 图谱扩展来源（直接命中为空）。
        item: 原始 EmbeddingItem（含向量与文本）。
        metadata: 附加元数据。
    """

    item_id: str = ""
    table_name: str = ""
    column_name: str = ""
    node_type: NodeType = NodeType.TABLE
    score: float = 0.0
    expanded_from: str = ""
    item: EmbeddingItem | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NL2SQLRequest(BaseModel):
    """NL2SQL 请求。

    Attributes:
        question: 自然语言问题。
        top_k: 语义检索召回数量。
        use_graph_expansion: 是否启用图谱 1-hop 扩展。
        include_lineage: 是否在 Prompt 注入血缘信息。
    """

    question: str
    top_k: int = 5
    use_graph_expansion: bool = True
    include_lineage: bool = False


class NL2SQLResponse(BaseModel):
    """NL2SQL 响应。

    Attributes:
        question: 原始问题。
        sql: 生成的 SQL。
        related_tables: 命中的相关表。
        join_paths: JOIN 路径详情列表。
        context: 组装的 LLM 上下文。
        confidence: 生成置信度 [0,1]。
        is_validated: 生成 SQL 是否通过解析校验。
        mock_mode: 是否为 Mock 模式产出。
    """

    question: str = ""
    sql: str
    related_tables: list[str] = Field(default_factory=list)
    join_paths: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    is_validated: bool = False
    mock_mode: bool = False

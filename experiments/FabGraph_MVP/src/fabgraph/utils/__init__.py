"""工具模块 (utils)。

跨层基础设施：LLM客户端、SQL解析、向量嵌入、异常体系。
对应ResNet中的辅助函数（归一化、激活等基础设施）。
"""
from __future__ import annotations

from fabgraph.utils.exceptions import (
    ConfigError,
    EmbeddingError,
    FabGraphError,
    GraphError,
    LLMError,
    MetadataError,
    NL2SQLError,
    SQLAnalysisError,
    SearchError,
)

__all__ = [
    "FabGraphError",
    "ConfigError",
    "MetadataError",
    "GraphError",
    "SQLAnalysisError",
    "SearchError",
    "EmbeddingError",
    "LLMError",
    "NL2SQLError",
]

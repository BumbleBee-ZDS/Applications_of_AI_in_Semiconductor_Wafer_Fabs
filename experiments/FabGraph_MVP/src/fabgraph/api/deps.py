"""API 依赖注入。

集中管理 service/repo 实例的创建与缓存，
路由通过 ``Depends(get_xxx)`` 获取依赖。
对应ResNet全局池化：跨请求共享已初始化的权重。
"""
from __future__ import annotations

import logging
from functools import lru_cache

from fabgraph.config import Settings, get_settings
from fabgraph.repository.graph_repo import GraphRepository
from fabgraph.repository.metadata_repo import MetadataRepository
from fabgraph.repository.vector_repo import VectorRepository
from fabgraph.service.graph_builder import BuildResult, GraphBuilderService
from fabgraph.service.nl2sql_service import NL2SQLService
from fabgraph.service.semantic_service import SemanticSearchService
from fabgraph.service.sql_analyzer import SqlAnalyzerService
from fabgraph.utils.embeddings import EmbeddingClient
from fabgraph.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

# 模块级缓存（单例）
_metadata_repo: MetadataRepository | None = None
_graph_repo: GraphRepository | None = None
_vector_repo: VectorRepository | None = None
_embedding_client: EmbeddingClient | None = None
_llm_client: LLMClient | None = None
_graph_builder: GraphBuilderService | None = None
_build_result: BuildResult | None = None
_semantic_service: SemanticSearchService | None = None
_nl2sql_service: NL2SQLService | None = None
_sql_analyzer: SqlAnalyzerService | None = None


def get_metadata_repo() -> MetadataRepository:
    """返回元数据仓储单例。"""
    global _metadata_repo
    if _metadata_repo is None:
        _metadata_repo = MetadataRepository()
    return _metadata_repo


def get_graph_repo() -> GraphRepository:
    """返回图谱仓储单例。"""
    global _graph_repo
    if _graph_repo is None:
        _graph_repo = GraphRepository()
    return _graph_repo


def get_vector_repo() -> VectorRepository:
    """返回向量仓储单例。"""
    global _vector_repo
    if _vector_repo is None:
        _vector_repo = VectorRepository()
    return _vector_repo


def get_embedding_client() -> EmbeddingClient:
    """返回嵌入客户端单例。"""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client


def get_llm_client() -> LLMClient:
    """返回 LLM 客户端单例。"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def get_graph_builder() -> GraphBuilderService:
    """返回图谱构建服务单例。"""
    global _graph_builder
    if _graph_builder is None:
        _graph_builder = GraphBuilderService(
            metadata_repo=get_metadata_repo(),
            graph_repo=get_graph_repo(),
        )
    return _graph_builder


def get_build_result() -> BuildResult:
    """返回已构建的图谱结果（首次调用时触发构建）。"""
    global _build_result
    if _build_result is None:
        _build_result = get_graph_builder().load_or_build(persist=True)
    return _build_result


def get_semantic_service() -> SemanticSearchService:
    """返回语义检索服务单例。"""
    global _semantic_service
    if _semantic_service is None:
        _semantic_service = SemanticSearchService(
            metadata_repo=get_metadata_repo(),
            vector_repo=get_vector_repo(),
            embedding_client=get_embedding_client(),
        )
        # 注入 Schema Graph
        try:
            result = get_build_result()
            _semantic_service.set_schema_graph(result.schema_graph)
        except Exception as e:
            logger.warning("注入 Schema Graph 失败: %s", e)
    return _semantic_service


def get_nl2sql_service() -> NL2SQLService:
    """返回 NL2SQL 服务单例。"""
    global _nl2sql_service
    if _nl2sql_service is None:
        _nl2sql_service = NL2SQLService(
            semantic_service=get_semantic_service(),
            llm_client=get_llm_client(),
            metadata_repo=get_metadata_repo(),
        )
    return _nl2sql_service


def get_sql_analyzer() -> SqlAnalyzerService:
    """返回 SQL 分析服务单例。"""
    global _sql_analyzer
    if _sql_analyzer is None:
        _sql_analyzer = SqlAnalyzerService(
            metadata_repo=get_metadata_repo()
        )
    return _sql_analyzer


def reset_dependencies() -> None:
    """重置全部单例（测试用）。"""
    global _metadata_repo, _graph_repo, _vector_repo
    global _embedding_client, _llm_client, _graph_builder
    global _build_result, _semantic_service, _nl2sql_service, _sql_analyzer
    for name in [
        "_metadata_repo", "_graph_repo", "_vector_repo",
        "_embedding_client", "_llm_client", "_graph_builder",
        "_build_result", "_semantic_service", "_nl2sql_service",
        "_sql_analyzer",
    ]:
        globals()[name] = None

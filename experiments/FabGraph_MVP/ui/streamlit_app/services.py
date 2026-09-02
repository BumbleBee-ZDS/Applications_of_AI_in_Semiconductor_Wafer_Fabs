"""Streamlit 服务初始化（带缓存）。

使用 ``@st.cache_resource`` 缓存 service 实例，
避免每次交互重复构建图谱/索引。
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# 确保 src 目录在 sys.path 中
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fabgraph.config import get_settings, reset_settings_cache  # noqa: E402
from fabgraph.repository.graph_repo import GraphRepository  # noqa: E402
from fabgraph.repository.metadata_repo import MetadataRepository  # noqa: E402
from fabgraph.repository.vector_repo import VectorRepository  # noqa: E402
from fabgraph.service.graph_builder import BuildResult, GraphBuilderService  # noqa: E402
from fabgraph.service.nl2sql_service import NL2SQLService  # noqa: E402
from fabgraph.service.semantic_service import SemanticSearchService  # noqa: E402
from fabgraph.service.sql_analyzer import SqlAnalyzerService  # noqa: E402
from fabgraph.utils.embeddings import EmbeddingClient  # noqa: E402
from fabgraph.utils.llm_client import LLMClient  # noqa: E402

logger = logging.getLogger(__name__)


@st.cache_resource
def get_settings_cached():
    """缓存配置。"""
    reset_settings_cache()
    return get_settings()


@st.cache_resource
def get_metadata_repo_cached():
    """缓存元数据仓储，首次自动加载 JSON。"""
    settings = get_settings_cached()
    repo = MetadataRepository(settings)
    if not repo.get_tables():
        repo.load_from_json()
    return repo


@st.cache_resource
def get_graph_repo_cached():
    """缓存图谱仓储。"""
    return GraphRepository(get_settings_cached())


@st.cache_resource
def get_build_result_cached():
    """缓存图谱构建结果。"""
    builder = GraphBuilderService(
        metadata_repo=get_metadata_repo_cached(),
        graph_repo=get_graph_repo_cached(),
        settings=get_settings_cached(),
    )
    return builder.load_or_build(persist=True)


@st.cache_resource
def get_embedding_client_cached():
    """缓存嵌入客户端。"""
    return EmbeddingClient(get_settings_cached())


@st.cache_resource
def get_vector_repo_cached():
    """缓存向量仓储。"""
    return VectorRepository(get_settings_cached())


@st.cache_resource
def get_llm_client_cached():
    """缓存 LLM 客户端。"""
    return LLMClient(get_settings_cached())


@st.cache_resource
def get_semantic_service_cached():
    """缓存语义检索服务。"""
    service = SemanticSearchService(
        metadata_repo=get_metadata_repo_cached(),
        vector_repo=get_vector_repo_cached(),
        embedding_client=get_embedding_client_cached(),
        settings=get_settings_cached(),
    )
    result = get_build_result_cached()
    service.set_schema_graph(result.schema_graph)
    return service


@st.cache_resource
def get_nl2sql_service_cached():
    """缓存 NL2SQL 服务。"""
    return NL2SQLService(
        semantic_service=get_semantic_service_cached(),
        llm_client=get_llm_client_cached(),
        metadata_repo=get_metadata_repo_cached(),
        settings=get_settings_cached(),
    )


@st.cache_resource
def get_sql_analyzer_cached():
    """缓存 SQL 分析服务。"""
    return SqlAnalyzerService(metadata_repo=get_metadata_repo_cached())

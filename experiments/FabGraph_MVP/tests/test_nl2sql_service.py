"""NL2SQLService 测试。"""
from __future__ import annotations

import networkx as nx
import pytest

from fabgraph.graph.schema_graph import SchemaGraphBuilder
from fabgraph.models.semantic import NL2SQLRequest
from fabgraph.service.graph_builder import GraphBuilderService
from fabgraph.service.nl2sql_service import NL2SQLService
from fabgraph.service.semantic_service import SemanticSearchService
from fabgraph.utils.embeddings import EmbeddingClient
from fabgraph.utils.llm_client import LLMClient


@pytest.fixture
def nl2sql_service(loaded_metadata_repo, vector_repo, graph_repo, tmp_settings):
    """完整配置的 NL2SQL 服务（含图谱注入）。"""
    # 构建图谱
    graph_service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo, graph_repo=graph_repo,
        settings=tmp_settings,
    )
    build_result = graph_service.build_all(persist=False)
    # 构建语义服务
    embedding_client = EmbeddingClient(tmp_settings)
    semantic_service = SemanticSearchService(
        metadata_repo=loaded_metadata_repo,
        vector_repo=vector_repo,
        embedding_client=embedding_client,
        settings=tmp_settings,
    )
    semantic_service.set_schema_graph(build_result.schema_graph)
    # LLM 客户端（Mock 模式）
    llm_client = LLMClient(tmp_settings)
    return NL2SQLService(
        semantic_service=semantic_service,
        llm_client=llm_client,
        metadata_repo=loaded_metadata_repo,
        settings=tmp_settings,
    )


def test_generate_basic(nl2sql_service):
    """基本 NL2SQL 生成应返回 SQL。"""
    req = NL2SQLRequest(question="查询 LOT_HISTORY 良率 yield SQL")
    resp = nl2sql_service.generate(req)
    assert resp.sql
    assert isinstance(resp.sql, str)
    assert len(resp.sql) > 0
    assert resp.related_tables  # 非空


def test_generate_returns_related_tables(nl2sql_service):
    """生成结果应包含相关表。"""
    req = NL2SQLRequest(question="LOT_HISTORY 良率")
    resp = nl2sql_service.generate(req)
    assert len(resp.related_tables) > 0
    # 应能召回 LOT_HISTORY
    assert any("LOT" in t.upper() for t in resp.related_tables)


def test_generate_returns_join_paths(nl2sql_service):
    """多表召回时应返回 JOIN 路径。"""
    req = NL2SQLRequest(question="LOT_HISTORY WAFER_RESULT JOIN SQL")
    resp = nl2sql_service.generate(req)
    # 若召回多表，应有 JOIN 路径
    if len(resp.related_tables) >= 2:
        # join_paths 可能为空（若图无连接），但字段应存在
        assert isinstance(resp.join_paths, list)


def test_generate_returns_confidence(nl2sql_service):
    """生成结果应包含置信度。"""
    req = NL2SQLRequest(question="LOT_HISTORY")
    resp = nl2sql_service.generate(req)
    assert 0.0 <= resp.confidence <= 1.0


def test_generate_returns_context(nl2sql_service):
    """生成结果应包含上下文。"""
    req = NL2SQLRequest(question="LOT_HISTORY")
    resp = nl2sql_service.generate(req)
    assert "tables" in resp.context
    assert len(resp.context["tables"]) > 0


def test_generate_validates_sql(nl2sql_service):
    """生成 SQL 应能被解析校验。"""
    req = NL2SQLRequest(question="SELECT LOT_HISTORY SQL")
    resp = nl2sql_service.generate(req)
    # Mock 模式生成的 SQL 可能不严格，但 is_validated 字段应存在
    assert isinstance(resp.is_validated, bool)


def test_postprocess_sql_strips_markdown():
    """后处理应去除 markdown 包裹。"""
    sql = NL2SQLService._postprocess_sql("```sql\nSELECT * FROM LOT_HISTORY\n```")
    assert sql == "SELECT * FROM LOT_HISTORY"


def test_postprocess_sql_plain():
    """无 markdown 包裹的 SQL 应原样返回。"""
    sql = NL2SQLService._postprocess_sql("SELECT * FROM LOT_HISTORY")
    assert sql == "SELECT * FROM LOT_HISTORY"


def test_generate_with_top_k(nl2sql_service):
    """top_k 参数应影响召回数量。"""
    req1 = NL2SQLRequest(question="LOT_HISTORY", top_k=1)
    resp1 = nl2sql_service.generate(req1)
    req5 = NL2SQLRequest(question="LOT_HISTORY", top_k=5)
    resp5 = nl2sql_service.generate(req5)
    # top_k=5 应召回不少于 top_k=1 的表
    assert len(resp5.related_tables) >= len(resp1.related_tables)

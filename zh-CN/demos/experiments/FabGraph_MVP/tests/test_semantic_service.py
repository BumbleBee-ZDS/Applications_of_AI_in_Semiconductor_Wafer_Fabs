"""SemanticSearchService 测试。"""
from __future__ import annotations

import networkx as nx
import pytest

from fabgraph.graph.schema_graph import SchemaGraphBuilder
from fabgraph.graph.graph_utils import table_node_id
from fabgraph.models.graph import NodeType
from fabgraph.models.schema import (
    Column,
    ColumnSemanticType,
    Procedure,
    Table,
)
from fabgraph.service.semantic_service import SemanticSearchService
from fabgraph.utils.embeddings import EmbeddingClient


def _make_table(name: str, desc: str, columns: list[Column]) -> Table:
    return Table(table_name=name, description=desc, columns=columns)


def _col(table: str, name: str, sem: ColumnSemanticType = ColumnSemanticType.UNKNOWN) -> Column:
    return Column(table_name=table, column_name=name, semantic_type=sem, description=name)


@pytest.fixture
def sample_tables() -> list[Table]:
    return [
        _make_table("LOT_HISTORY", "批次历史 良率 yield", [
            _col("LOT_HISTORY", "LOT_ID", ColumnSemanticType.PRIMARY_KEY),
            _col("LOT_HISTORY", "YIELD_VAL", ColumnSemanticType.MEASURE),
        ]),
        _make_table("WAFER_RESULT", "晶圆测试结果 defect 缺陷", [
            _col("WAFER_RESULT", "WFR_ID", ColumnSemanticType.PRIMARY_KEY),
            _col("WAFER_RESULT", "DEFECT_CNT", ColumnSemanticType.MEASURE),
        ]),
    ]


@pytest.fixture
def sample_procedures() -> list[Procedure]:
    return [
        Procedure(procedure_name="SP_CALC_YIELD", description="计算良率",
                  input_tables=["LOT_HISTORY"], output_tables=["WAFER_RESULT"]),
    ]


@pytest.fixture
def semantic_service(
    loaded_metadata_repo, vector_repo, tmp_settings
):
    """基于已加载元数据的语义服务。"""
    client = EmbeddingClient(tmp_settings)
    return SemanticSearchService(
        metadata_repo=loaded_metadata_repo,
        vector_repo=vector_repo,
        embedding_client=client,
        settings=tmp_settings,
    )


def test_index_metadata(semantic_service):
    """索引构建应返回非零项数。"""
    n = semantic_service.index_metadata()
    assert n > 0
    # 应包含表和字段
    assert len(semantic_service.vector_repo) > 0


def test_search_returns_results(semantic_service):
    """检索应返回非空结果（Mock 嵌入不保证语义精度，仅验证管线）。"""
    semantic_service.index_metadata()
    results = semantic_service.search("良率 yield", top_k=10, expand=False)
    assert len(results) > 0
    # 所有结果应有非空文本
    for r in results:
        assert r.item.text
        assert r.score >= 0.0


def test_search_tables_only(semantic_service):
    """search_tables 应仅返回表级结果。"""
    semantic_service.index_metadata()
    results = semantic_service.search_tables("良率", top_k=5, expand=False)
    assert len(results) > 0
    for r in results:
        assert r.node_type == NodeType.TABLE


def test_search_with_graph_expansion(semantic_service, loaded_metadata_repo):
    """图扩展应增加字段级结果。"""
    # 构建并注入 Schema Graph
    tables = loaded_metadata_repo.get_tables()
    procs = loaded_metadata_repo.get_procedures()
    sg = SchemaGraphBuilder().build(tables, procs)
    semantic_service.set_schema_graph(sg)
    semantic_service.index_metadata()
    results = semantic_service.search("LOT_HISTORY", top_k=2, expand=True)
    # 扩展后应包含字段节点
    assert any(r.node_type == NodeType.COLUMN for r in results)


def test_search_empty_question(semantic_service):
    """空问题仍应返回结果（不报错）。"""
    semantic_service.index_metadata()
    results = semantic_service.search("", top_k=3, expand=False)
    assert isinstance(results, list)


def test_search_auto_index(semantic_service):
    """未显式 index 时检索应自动触发索引构建。"""
    results = semantic_service.search("defect", top_k=3, expand=False)
    assert len(results) > 0

"""GraphBuilderService 端到端测试。"""
from __future__ import annotations

import networkx as nx
import pytest

from fabgraph.service.graph_builder import BuildResult, GraphBuilderService
from fabgraph.utils.exceptions import GraphError


def test_build_all_with_mock_data(loaded_metadata_repo, graph_repo):
    """加载 mock 数据后构建图谱应返回非空结果。"""
    service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo,
        graph_repo=graph_repo,
    )
    result = service.build_all(persist=False)
    assert isinstance(result, BuildResult)
    assert result.table_count == 8
    assert result.procedure_count == 6
    # Schema Graph 应包含 table/column/procedure 节点
    assert result.schema_graph.number_of_nodes() > 0
    # Lineage Graph 应包含超边
    assert len(result.hyperedges) == 6
    # JOIN 图应包含 FK 边
    assert result.join_graph.number_of_edges() > 0
    # 摘要
    summary = result.summary()
    assert summary["tables"] == 8
    assert summary["procedures"] == 6
    assert summary["schema_nodes"] > 0


def test_build_all_persists_pickle(loaded_metadata_repo, graph_repo):
    """persist=True 应生成 pickle 文件。"""
    service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo, graph_repo=graph_repo,
    )
    service.build_all(persist=True)
    status = graph_repo.exists()
    assert status["schema_graph"] is True
    assert status["lineage_graph"] is True


def test_load_or_build_when_no_snapshot(loaded_metadata_repo, graph_repo):
    """无快照时应触发构建。"""
    service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo, graph_repo=graph_repo,
    )
    result = service.load_or_build(persist=True)
    assert result.table_count == 8
    assert graph_repo.exists()["schema_graph"] is True


def test_load_or_build_uses_existing_snapshot(loaded_metadata_repo, graph_repo):
    """已有快照时应直接加载。"""
    # 第一次构建并持久化
    service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo, graph_repo=graph_repo,
    )
    service.build_all(persist=True)
    # 第二次应加载快照
    result = service.load_or_build()
    assert result.schema_graph.number_of_nodes() > 0
    assert len(result.hyperedges) == 6


def test_build_all_empty_metadata_raises(metadata_repo, graph_repo):
    """空元数据应抛 GraphError。"""
    # metadata_repo 已 init 但未 load
    service = GraphBuilderService(
        metadata_repo=metadata_repo, graph_repo=graph_repo,
    )
    with pytest.raises(GraphError):
        service.build_all()


def test_build_all_with_semantic_hints(loaded_metadata_repo, graph_repo):
    """注入 semantic_hints 应生成 join_inferred 边。"""
    from fabgraph.models.schema import SemanticHint

    hints = [
        SemanticHint(
            table_name="LOT_HISTORY",
            column_name="LOT_ID",
            hint_type="join_key",
            hint_value="YIELD_SUMMARY.LOT_ID",
            confidence=0.9,
        ),
    ]
    service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo, graph_repo=graph_repo,
    )
    result = service.build_all(semantic_hints=hints, persist=False)
    # 应包含 join_inferred 边
    from fabgraph.models.graph import EdgeType
    join_edges = [
        e for e in result.schema_graph.edges(data=True)
        if e[2].get("edge_type") == EdgeType.JOIN_INFERRED
    ]
    assert len(join_edges) >= 2  # 双向


def test_load_or_build_falls_back_on_corrupt(loaded_metadata_repo, graph_repo):
    """快照损坏时应回退到重新构建。"""
    service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo, graph_repo=graph_repo,
    )
    service.build_all(persist=True)
    # 损坏 schema_graph pickle
    with open(graph_repo.schema_graph_path, "wb") as f:
        f.write(b"corrupt")
    # 应回退到重新构建（不抛错）
    result = service.load_or_build()
    assert result.schema_graph.number_of_nodes() > 0


def test_join_path_finder_on_built_graph(loaded_metadata_repo, graph_repo):
    """构建后的 JOIN 图应能查找路径。"""
    from fabgraph.graph.graph_algorithms import JoinPathFinder

    service = GraphBuilderService(
        metadata_repo=loaded_metadata_repo, graph_repo=graph_repo,
    )
    result = service.build_all(persist=False)
    finder = JoinPathFinder(result.join_graph)
    # LOT_HISTORY 与 WAFER_RESULT 应有 FK 连接（通过 WFR_ID）
    p = finder.find_path("LOT_HISTORY", "WAFER_RESULT")
    assert "LOT_HISTORY" in p.path
    assert "WAFER_RESULT" in p.path

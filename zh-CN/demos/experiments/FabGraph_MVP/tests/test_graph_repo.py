"""GraphRepository 测试。"""
from __future__ import annotations

import networkx as nx
import pytest

from fabgraph.utils.exceptions import GraphError


def test_save_and_load_schema_graph(graph_repo):
    """Schema Graph 保存与加载应一致。"""
    g = nx.MultiDiGraph()
    g.add_node("table:A", node_type="table", name="A")
    g.add_node("table:B", node_type="table", name="B")
    g.add_edge("table:A", "table:B", edge_type="foreign_key", weight=0.5)

    path = graph_repo.save_schema_graph(g)
    assert path.exists()

    loaded = graph_repo.load_schema_graph()
    assert loaded is not None
    assert loaded.number_of_nodes() == 2
    assert loaded.number_of_edges() == 1
    # 边属性保留
    edge_data = loaded.get_edge_data("table:A", "table:B")[0]
    assert edge_data["weight"] == 0.5


def test_save_and_load_lineage_graph(graph_repo):
    """Lineage Graph 含超边属性应能持久化。"""
    g = nx.MultiDiGraph()
    g.graph["hyperedges"] = {"hyper:P1": {"edge_id": "hyper:P1"}}
    g.add_node("table:A")
    g.add_node("procedure:P1")
    g.add_edge("procedure:P1", "table:A", edge_type="reads")

    graph_repo.save_lineage_graph(g)
    loaded = graph_repo.load_lineage_graph()
    assert loaded is not None
    assert "hyperedges" in loaded.graph
    assert "hyper:P1" in loaded.graph["hyperedges"]


def test_load_nonexistent(graph_repo):
    """文件不存在时返回 None。"""
    assert graph_repo.load_schema_graph() is None
    assert graph_repo.load_lineage_graph() is None


def test_exists(graph_repo):
    """exists 反映文件存在情况。"""
    status = graph_repo.exists()
    assert status["schema_graph"] is False
    assert status["lineage_graph"] is False

    g = nx.Graph()
    g.add_node("x")
    graph_repo.save_schema_graph(g)

    status = graph_repo.exists()
    assert status["schema_graph"] is True
    assert status["lineage_graph"] is False


def test_corrupt_pickle_raises(graph_repo, tmp_path):
    """损坏的 pickle 文件应抛 GraphError。"""
    # 写入损坏内容
    with open(graph_repo.schema_graph_path, "wb") as f:
        f.write(b"not a pickle")
    with pytest.raises(GraphError):
        graph_repo.load_schema_graph()

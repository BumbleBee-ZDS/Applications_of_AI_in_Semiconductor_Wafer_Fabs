"""graph_algorithms 测试。"""
from __future__ import annotations

import networkx as nx
import pytest

from fabgraph.graph.graph_algorithms import (
    JoinPathFinder,
    detect_communities,
    get_community_members,
    list_communities,
)
from fabgraph.graph.graph_utils import project_lineage_to_undirected
from fabgraph.models.graph import EdgeType
from fabgraph.utils.exceptions import NL2SQLError


def _make_join_graph() -> nx.Graph:
    """构造测试用 JOIN 图：
    A -- B -- C -- D
    """
    g = nx.Graph()
    g.add_node("table:A")
    g.add_node("table:B")
    g.add_node("table:C")
    g.add_node("table:D")
    g.add_edge("table:A", "table:B", weight=1.0, join_condition="A.x = B.x",
               conditions=["A.x = B.x"])
    g.add_edge("table:B", "table:C", weight=1.0, join_condition="B.y = C.y",
               conditions=["B.y = C.y"])
    g.add_edge("table:C", "table:D", weight=1.0, join_condition="C.z = D.z",
               conditions=["C.z = D.z"])
    return g


def test_find_path_simple():
    """两表直连应返回单跳路径。"""
    finder = JoinPathFinder(_make_join_graph())
    p = finder.find_path("A", "B")
    assert p.start_table == "A"
    assert p.end_table == "B"
    assert p.path == ["A", "B"]
    assert len(p.join_conditions) == 1
    assert p.total_weight == 1.0


def test_find_path_multi_hop():
    """多跳路径应正确返回全部中间表与条件。"""
    finder = JoinPathFinder(_make_join_graph())
    p = finder.find_path("A", "D")
    assert p.path == ["A", "B", "C", "D"]
    assert len(p.join_conditions) == 3
    assert p.total_weight == 3.0


def test_find_path_same_table():
    """起止表相同应返回空路径。"""
    finder = JoinPathFinder(_make_join_graph())
    p = finder.find_path("A", "A")
    assert p.path == ["A"]
    assert p.join_conditions == []
    assert p.total_weight == 0.0


def test_find_path_no_path():
    """不连通的表应抛 NL2SQLError。"""
    g = _make_join_graph()
    g.add_node("table:ISO")
    finder = JoinPathFinder(g)
    with pytest.raises(NL2SQLError):
        finder.find_path("A", "ISO")


def test_find_path_unknown_table():
    """未注册表应抛 NL2SQLError。"""
    finder = JoinPathFinder(_make_join_graph())
    with pytest.raises(NL2SQLError):
        finder.find_path("A", "NOT_EXIST")


def test_find_path_max_hops_exceeded():
    """超过最大跳数应抛 NL2SQLError。"""
    finder = JoinPathFinder(_make_join_graph())
    with pytest.raises(NL2SQLError):
        finder.find_path("A", "D", max_hops=1)


def test_find_multi_table_path():
    """多表连通应返回 len-1 条路径。"""
    finder = JoinPathFinder(_make_join_graph())
    paths = finder.find_multi_table_path(["A", "D", "B"], max_hops=3)
    assert len(paths) == 2
    all_tables = {p.end_table for p in paths}
    assert all_tables == {"D", "B"}


def test_find_multi_table_single_table():
    """单表输入应返回空列表。"""
    finder = JoinPathFinder(_make_join_graph())
    assert finder.find_multi_table_path(["A"]) == []


def test_detect_communities_empty():
    """空图社区检测返回空字典。"""
    assert detect_communities(nx.Graph()) == {}


def test_detect_communities_girvan_newman():
    """Girvan-Newman 应能划分社区。"""
    # 构造两个明显的簇，由一条桥边相连
    g = nx.Graph()
    g.add_edges_from([
        ("A", "B"), ("B", "C"), ("A", "C"),  # 簇 1
        ("D", "E"), ("E", "F"), ("D", "F"),  # 簇 2
        ("C", "D"),  # 桥
    ])
    partition = detect_communities(g, method="girvan_newman")
    assert len(partition) == 6
    # 簇 1 与簇 2 应属于不同社区
    assert partition["A"] == partition["B"] == partition["C"]
    assert partition["D"] == partition["E"] == partition["F"]
    assert partition["A"] != partition["D"]


def test_detect_communities_auto_method():
    """auto 方法应正常返回（louvain 或 girvan_newman）。"""
    g = nx.Graph()
    g.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
    partition = detect_communities(g, method="auto")
    assert len(partition) == 3
    # 三角形是连通图，社区数应 <= 2（Girvan-Newman 可能切一刀）
    assert len(set(partition.values())) <= 2


def test_detect_communities_unsupported_method():
    """不支持的社区检测方法应抛 GraphError。"""
    g = nx.Graph()
    g.add_edge("A", "B")
    from fabgraph.utils.exceptions import GraphError
    with pytest.raises(GraphError):
        detect_communities(g, method="bogus")


def test_list_communities():
    """社区分组。"""
    partition = {"A": 0, "B": 0, "C": 1, "D": 1}
    grouped = list_communities(partition)
    assert set(grouped[0]) == {"A", "B"}
    assert set(grouped[1]) == {"C", "D"}


def test_get_community_members():
    """按社区 id 取成员。"""
    partition = {"A": 0, "B": 1, "C": 0}
    members = get_community_members(partition, 0)
    assert set(members) == {"A", "C"}


def test_project_lineage_to_undirected():
    """Lineage MultiDiGraph 投影为无向图。"""
    g = nx.MultiDiGraph()
    g.add_node("table:A")
    g.add_node("table:B")
    g.add_node("procedure:P1")
    g.add_edge("procedure:P1", "table:A", edge_type=EdgeType.READS)
    g.add_edge("procedure:P1", "table:B", edge_type=EdgeType.WRITES)
    g.add_edge("table:A", "table:B", edge_type=EdgeType.LINEAGE)

    undirected = project_lineage_to_undirected(g)
    assert undirected.number_of_nodes() == 3
    assert undirected.number_of_edges() == 3
    # 无向图
    assert isinstance(undirected, nx.Graph)
    assert not undirected.is_directed()

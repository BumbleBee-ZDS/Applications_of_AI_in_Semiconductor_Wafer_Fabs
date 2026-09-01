"""LineageGraphBuilder 测试。"""
from __future__ import annotations

import pytest

from fabgraph.graph.lineage_graph import (
    LineageGraphBuilder,
    get_downstream_tables,
    get_hyperedges,
    get_upstream_tables,
    parse_table_name,
)
from fabgraph.models.graph import EdgeType, NodeType
from fabgraph.models.schema import Procedure, Table
from fabgraph.utils.exceptions import GraphError


def _make_table(name: str) -> Table:
    return Table(table_name=name, description=f"table {name}")


@pytest.fixture
def sample_tables() -> list[Table]:
    return [_make_table("A"), _make_table("B"), _make_table("C")]


@pytest.fixture
def sample_procedures() -> list[Procedure]:
    """P1: A -> B; P2: B -> C; P3: A,C -> B (多输入)。"""
    return [
        Procedure(procedure_name="P1", input_tables=["A"], output_tables=["B"]),
        Procedure(procedure_name="P2", input_tables=["B"], output_tables=["C"]),
        Procedure(
            procedure_name="P3", input_tables=["A", "C"], output_tables=["B"],
        ),
    ]


def test_build_basic(sample_tables, sample_procedures):
    """构建图谱应包含 table/procedure 节点与 reads/writes 边。"""
    g = LineageGraphBuilder().build(sample_tables, sample_procedures)
    # 节点
    assert g.number_of_nodes() == 6  # 3 表 + 3 过程
    # reads 边: P1->A, P2->B, P3->A, P3->C = 4
    reads = [
        e for e in g.edges(data=True) if e[2].get("edge_type") == EdgeType.READS
    ]
    assert len(reads) == 4
    # writes 边: P1->B, P2->C, P3->B = 3
    writes = [
        e for e in g.edges(data=True) if e[2].get("edge_type") == EdgeType.WRITES
    ]
    assert len(writes) == 3


def test_hyperedges(sample_tables, sample_procedures):
    """每个过程应生成一个超边。"""
    g = LineageGraphBuilder().build(sample_tables, sample_procedures)
    hypers = get_hyperedges(g)
    assert len(hypers) == 3
    assert "hyper:P1" in hypers
    p1 = hypers["hyper:P1"]
    assert p1.procedure_name == "P1"
    assert p1.source_tables == ["A"]
    assert p1.target_tables == ["B"]


def test_lineage_edges(sample_tables, sample_procedures):
    """lineage 边由过程 input -> output 推导。"""
    g = LineageGraphBuilder().build(sample_tables, sample_procedures)
    lineage = [
        e for e in g.edges(data=True) if e[2].get("edge_type") == EdgeType.LINEAGE
    ]
    # P1: A->B; P2: B->C; P3: A->B, C->B (自环跳过无) => 4 条
    assert len(lineage) == 4
    # 验证 A->B 存在
    pairs = {(e[0], e[1]) for e in lineage}
    assert ("table:A", "table:B") in pairs
    assert ("table:B", "table:C") in pairs


def test_upstream_downstream(sample_tables, sample_procedures):
    """上下游表遍历应递归沿 lineage 边。"""
    g = LineageGraphBuilder().build(sample_tables, sample_procedures)
    # C 的上游：B（直接），A（间接，通过 P1 和 P3）
    upstream = set(get_upstream_tables(g, "C"))
    assert "B" in upstream
    assert "A" in upstream
    # A 的下游：B（直接），C（间接）
    downstream = set(get_downstream_tables(g, "A"))
    assert "B" in downstream
    assert "C" in downstream


def test_unknown_table_returns_empty(sample_tables, sample_procedures):
    """未注册的表应返回空列表。"""
    g = LineageGraphBuilder().build(sample_tables, sample_procedures)
    assert get_upstream_tables(g, "NOT_EXIST") == []
    assert get_downstream_tables(g, "NOT_EXIST") == []


def test_self_loop_skipped(sample_tables):
    """过程 input == output 时应跳过 lineage 自环。"""
    procs = [
        Procedure(procedure_name="P_SELF", input_tables=["A"], output_tables=["A"]),
    ]
    g = LineageGraphBuilder().build(sample_tables, procs)
    lineage = [
        e for e in g.edges(data=True) if e[2].get("edge_type") == EdgeType.LINEAGE
    ]
    assert lineage == []


def test_unregistered_table_warns(sample_tables):
    """过程引用未注册表应跳过且不报错。"""
    procs = [
        Procedure(
            procedure_name="P_BAD",
            input_tables=["A", "UNKNOWN_TABLE"],
            output_tables=["B"],
        ),
    ]
    g = LineageGraphBuilder().build(sample_tables, procs)
    # 仅 A -> B 一条 lineage（UNKNOWN_TABLE 被跳过）
    lineage = [
        e for e in g.edges(data=True) if e[2].get("edge_type") == EdgeType.LINEAGE
    ]
    assert len(lineage) == 1


def test_get_hyperedges_on_wrong_graph():
    """对无超边属性的图调用应抛 GraphError。"""
    import networkx as nx
    g = nx.MultiDiGraph()
    with pytest.raises(GraphError):
        get_hyperedges(g)


def test_parse_table_name():
    """table 节点 id 解析为表名。"""
    assert parse_table_name("table:LOT_HISTORY") == "LOT_HISTORY"
    assert parse_table_name("LOT_HISTORY") == "LOT_HISTORY"

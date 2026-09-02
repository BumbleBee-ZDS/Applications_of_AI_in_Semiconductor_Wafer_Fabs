"""SchemaGraphBuilder 测试。"""
from __future__ import annotations

import networkx as nx
import pytest

from fabgraph.graph.schema_graph import SchemaGraphBuilder
from fabgraph.graph.graph_utils import (
    column_node_id,
    parse_node_id,
    procedure_node_id,
    table_node_id,
    to_graph_node,
    to_join_graph,
)
from fabgraph.models.graph import EdgeType, NodeType
from fabgraph.models.schema import (
    Column,
    ColumnSemanticType,
    Procedure,
    SemanticHint,
    Table,
)
from fabgraph.utils.exceptions import GraphError


def _make_table(name: str, columns: list[Column]) -> Table:
    return Table(table_name=name, description=f"table {name}", columns=columns)


def _make_column(
    table_name: str, name: str,
    sem: ColumnSemanticType = ColumnSemanticType.UNKNOWN,
    pos: int = 1,
) -> Column:
    return Column(table_name=table_name, column_name=name, semantic_type=sem, position=pos)


@pytest.fixture
def sample_tables() -> list[Table]:
    """构造两张表：LOT_HISTORY(LOT_ID pk, WFR_ID fk) + WAFER_RESULT(WFR_ID pk)。"""
    return [
        _make_table("LOT_HISTORY", [
            _make_column("LOT_HISTORY", "LOT_ID", ColumnSemanticType.PRIMARY_KEY, 1),
            _make_column("LOT_HISTORY", "WFR_ID", ColumnSemanticType.FOREIGN_KEY, 2),
        ]),
        _make_table("WAFER_RESULT", [
            _make_column("WAFER_RESULT", "WFR_ID", ColumnSemanticType.PRIMARY_KEY, 1),
            _make_column("WAFER_RESULT", "YIELD_VAL", ColumnSemanticType.MEASURE, 2),
        ]),
    ]


def test_build_basic(sample_tables):
    """构建图谱应包含 table/column 节点与 has_column 边。"""
    builder = SchemaGraphBuilder()
    g = builder.build(sample_tables)
    # table 节点
    assert table_node_id("LOT_HISTORY") in g
    assert table_node_id("WAFER_RESULT") in g
    # column 节点
    assert column_node_id("LOT_HISTORY", "LOT_ID") in g
    assert column_node_id("WAFER_RESULT", "WFR_ID") in g
    # has_column 边
    has_col_edges = [
        (u, v) for u, v, d in g.edges(data=True)
        if d.get("edge_type") == EdgeType.HAS_COLUMN
    ]
    assert len(has_col_edges) == 4  # 2 + 2 字段


def test_foreign_key_edges(sample_tables):
    """FK 字段应建立 column -> PK column 的 foreign_key 边。"""
    builder = SchemaGraphBuilder()
    g = builder.build(sample_tables)
    fk_edges = [
        (u, v) for u, v, d in g.edges(data=True)
        if d.get("edge_type") == EdgeType.FOREIGN_KEY
    ]
    assert len(fk_edges) == 1
    src, dst = fk_edges[0]
    assert src == column_node_id("LOT_HISTORY", "WFR_ID")
    assert dst == column_node_id("WAFER_RESULT", "WFR_ID")


def test_procedure_nodes(sample_tables):
    """过程作为独立实体节点加入 schema graph。"""
    proc = Procedure(
        procedure_name="SP_TEST",
        input_tables=["LOT_HISTORY"],
        output_tables=["WAFER_RESULT"],
    )
    g = SchemaGraphBuilder().build(sample_tables, [proc])
    assert procedure_node_id("SP_TEST") in g
    # schema graph 中过程节点不应与 table 连边
    proc_edges = [
        (u, v) for u, v, d in g.edges(data=True)
        if u == procedure_node_id("SP_TEST") or v == procedure_node_id("SP_TEST")
    ]
    assert proc_edges == []


def test_join_inferred_edges(sample_tables):
    """join_key 语义提示应生成双向 join_inferred 边。"""
    hint = SemanticHint(
        table_name="LOT_HISTORY", column_name="LOT_ID",
        hint_type="join_key", hint_value="YIELD_SUMMARY.LOT_ID",
        confidence=0.9,
    )
    # 增加一张表 YIELD_SUMMARY 才能让 hint_value 命中
    tables = sample_tables + [
        _make_table("YIELD_SUMMARY", [
            _make_column("YIELD_SUMMARY", "LOT_ID", ColumnSemanticType.PRIMARY_KEY, 1),
        ]),
    ]
    g = SchemaGraphBuilder().build(tables, semantic_hints=[hint])
    join_edges = [
        (u, v, d) for u, v, d in g.edges(data=True)
        if d.get("edge_type") == EdgeType.JOIN_INFERRED
    ]
    assert len(join_edges) == 2  # 双向


def test_to_join_graph(sample_tables):
    """投影的 JOIN 图应是 table-level 无向图。"""
    g = SchemaGraphBuilder().build(sample_tables)
    jg = to_join_graph(g)
    assert jg.number_of_nodes() == 2  # 2 张表
    assert jg.number_of_edges() == 1  # FK 形成 1 条 join 边
    # 边属性包含 join_condition
    edge = jg.edges[table_node_id("LOT_HISTORY"), table_node_id("WAFER_RESULT")]
    assert "join_condition" in edge
    assert "weight" in edge


def test_parse_node_id():
    """节点 id 解析。"""
    assert parse_node_id(table_node_id("LOT")) == (NodeType.TABLE, "LOT")
    assert parse_node_id(column_node_id("LOT", "ID")) == (NodeType.COLUMN, "LOT.ID")
    assert parse_node_id(procedure_node_id("SP")) == (NodeType.PROCEDURE, "SP")
    with pytest.raises(GraphError):
        parse_node_id("unknown:X")


def test_to_graph_node(sample_tables):
    """节点转 GraphNode 模型。"""
    g = SchemaGraphBuilder().build(sample_tables)
    node = to_graph_node(table_node_id("LOT_HISTORY"), g)
    assert node.node_type == NodeType.TABLE
    assert node.name == "LOT_HISTORY"
    assert "description" in node.properties


def test_fk_infer_ref_table_suffixes():
    """FK 命名启发式覆盖 _ID/_CD/_KEY 后缀及 _HISTORY 扩展。"""
    builder = SchemaGraphBuilder()
    tables = {"LOT_HISTORY", "WAFER_RESULT", "EQUIPMENT"}
    # LOT_ID -> LOT -> LOT_HISTORY（_HISTORY 扩展匹配）
    assert builder._infer_ref_table("LOT_ID", tables) == "LOT_HISTORY"
    # 直接前缀命中
    assert builder._infer_ref_table("LOT_HISTORY_ID", tables) == "LOT_HISTORY"
    assert builder._infer_ref_table("EQUIPMENT_ID", tables) == "EQUIPMENT"
    # 完全不匹配的应返回 None
    assert builder._infer_ref_table("FOO_BAR", tables) is None

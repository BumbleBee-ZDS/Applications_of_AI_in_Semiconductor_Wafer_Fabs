"""SQL 解析器测试。"""
from __future__ import annotations

import pytest

from fabgraph.utils.exceptions import SQLAnalysisError
from fabgraph.utils.sql_parser import SqlParser, parse_sql


def test_parse_simple_select():
    """简单 SELECT 解析。"""
    sql = "SELECT LOT_ID, PRODUCT_ID FROM LOT_HISTORY WHERE LOT_ID = 'L001'"
    parsed = parse_sql(sql)
    assert parsed.category == "select"
    assert len(parsed.tables) == 1
    assert parsed.tables[0].name == "LOT_HISTORY"
    assert len(parsed.columns) >= 2
    assert any(c.name == "LOT_ID" for c in parsed.columns)


def test_parse_with_alias():
    """表别名解析。"""
    sql = "SELECT l.LOT_ID FROM LOT_HISTORY l WHERE l.LOT_ID = 'L001'"
    parsed = parse_sql(sql)
    assert len(parsed.tables) == 1
    assert parsed.tables[0].name == "LOT_HISTORY"
    assert parsed.tables[0].alias == "L"


def test_parse_join():
    """JOIN 条件解析。"""
    sql = (
        "SELECT l.LOT_ID, w.YIELD_VAL FROM LOT_HISTORY l "
        "JOIN WAFER_RESULT w ON l.WFR_ID = w.WFR_ID"
    )
    parsed = parse_sql(sql)
    assert len(parsed.tables) == 2
    names = {t.name for t in parsed.tables}
    assert names == {"LOT_HISTORY", "WAFER_RESULT"}
    assert len(parsed.joins) == 1
    join = parsed.joins[0]
    assert join.left_column == "WFR_ID"
    assert join.right_column == "WFR_ID"


def test_parse_aggregation():
    """聚合函数解析。"""
    sql = (
        "SELECT PRODUCT_ID, AVG(YIELD_VAL) as avg_yield "
        "FROM WAFER_RESULT GROUP BY PRODUCT_ID"
    )
    parsed = parse_sql(sql)
    assert len(parsed.aggregations) == 1
    agg = parsed.aggregations[0]
    assert agg["func"] == "AVG"
    assert agg["column"] == "YIELD_VAL"
    assert agg["alias"] == "avg_yield"


def test_parse_count_star():
    """COUNT(*) 聚合。"""
    sql = "SELECT COUNT(*) FROM LOT_HISTORY"
    parsed = parse_sql(sql)
    assert len(parsed.aggregations) == 1
    assert parsed.aggregations[0]["column"] == "*"


def test_parse_insert():
    """INSERT 语句解析目标表。"""
    sql = (
        "INSERT INTO YIELD_SUMMARY (LOT_ID, YIELD_VAL) "
        "SELECT LOT_ID, YIELD_VAL FROM WAFER_RESULT"
    )
    parsed = parse_sql(sql)
    assert parsed.category == "insert"
    assert parsed.target_table == "YIELD_SUMMARY"


def test_parse_where_filters():
    """WHERE 条件解析。"""
    sql = (
        "SELECT * FROM LOT_HISTORY "
        "WHERE LOT_ID = 'L001' AND PRODUCT_ID = 'P1'"
    )
    parsed = parse_sql(sql)
    assert len(parsed.filters) >= 1


def test_parse_invalid_sql():
    """非法 SQL 应抛 SQLAnalysisError。"""
    with pytest.raises(SQLAnalysisError):
        parse_sql("SELECT FROM WHERE")


def test_parse_empty():
    """空 SQL 返回空结果。"""
    parsed = parse_sql("")
    assert parsed.tables == []
    assert parsed.columns == []


def test_parse_multi_join():
    """多表 JOIN 解析。"""
    sql = (
        "SELECT * FROM LOT_HISTORY l "
        "JOIN WAFER_RESULT w ON l.WFR_ID = w.WFR_ID "
        "JOIN EQUIPMENT_LOG e ON w.EQP_ID = e.EQP_ID"
    )
    parsed = parse_sql(sql)
    assert len(parsed.tables) == 3
    assert len(parsed.joins) == 2


def test_parse_left_join():
    """LEFT JOIN 类型识别。"""
    sql = (
        "SELECT * FROM LOT_HISTORY l "
        "LEFT JOIN WAFER_RESULT w ON l.WFR_ID = w.WFR_ID"
    )
    parsed = parse_sql(sql)
    assert len(parsed.joins) == 1
    assert "LEFT" in parsed.joins[0].join_type.upper()

"""SqlAnalyzerService 测试。"""
from __future__ import annotations

import pytest

from fabgraph.service.sql_analyzer import SqlAnalyzerService


def test_analyze_join_sql():
    """JOIN SQL 应生成 join_key 提示。"""
    sql = (
        "SELECT l.LOT_ID FROM LOT_HISTORY l "
        "JOIN WAFER_RESULT w ON l.WFR_ID = w.WFR_ID"
    )
    service = SqlAnalyzerService()
    hints = service.analyze(sql)
    join_hints = [h for h in hints if h.hint_type == "join_key"]
    assert len(join_hints) >= 2  # 双向
    # 验证 hint_value 包含对端字段引用
    assert any("WAFER_RESULT.WFR_ID" in h.hint_value for h in join_hints)


def test_analyze_aggregate_sql():
    """聚合 SQL 应生成 aggregate 提示。"""
    sql = "SELECT AVG(YIELD_VAL) FROM WAFER_RESULT"
    service = SqlAnalyzerService()
    hints = service.analyze(sql)
    agg_hints = [h for h in hints if h.hint_type == "aggregate"]
    assert len(agg_hints) == 1
    assert agg_hints[0].column_name == "YIELD_VAL"
    assert agg_hints[0].hint_value == "AVG"


def test_analyze_filter_sql():
    """WHERE 条件应生成 filter 提示。"""
    sql = "SELECT * FROM LOT_HISTORY l WHERE l.LOT_ID = 'L001'"
    service = SqlAnalyzerService()
    hints = service.analyze(sql)
    filter_hints = [h for h in hints if h.hint_type == "filter"]
    assert len(filter_hints) >= 1
    assert filter_hints[0].column_name == "LOT_ID"


def test_analyze_alias_sql():
    """表别名应生成 alias 提示。"""
    sql = "SELECT l.LOT_ID FROM LOT_HISTORY l"
    service = SqlAnalyzerService()
    hints = service.analyze(sql)
    alias_hints = [h for h in hints if h.hint_type == "alias"]
    assert len(alias_hints) == 1
    assert alias_hints[0].table_name == "LOT_HISTORY"
    assert alias_hints[0].hint_value == "L"


def test_analyze_insert_lineage():
    """INSERT...SELECT 应生成 lineage 提示。"""
    sql = (
        "INSERT INTO YIELD_SUMMARY (LOT_ID) "
        "SELECT LOT_ID FROM WAFER_RESULT"
    )
    service = SqlAnalyzerService()
    hints = service.analyze(sql)
    lineage_hints = [h for h in hints if h.hint_type == "lineage"]
    assert len(lineage_hints) == 1
    assert lineage_hints[0].table_name == "WAFER_RESULT"
    assert lineage_hints[0].hint_value == "YIELD_SUMMARY"


def test_analyze_batch():
    """批量分析多条 SQL。"""
    sqls = [
        {"sql": "SELECT * FROM LOT_HISTORY"},
        {"sql": "SELECT l.LOT_ID FROM LOT_HISTORY l JOIN WAFER_RESULT w ON l.WFR_ID = w.WFR_ID"},
    ]
    service = SqlAnalyzerService()
    hints = service.analyze_batch(sqls)
    assert len(hints) > 0
    # 应包含 join_key 提示
    assert any(h.hint_type == "join_key" for h in hints)


def test_analyze_batch_skips_invalid():
    """批量分析应跳过无法解析的 SQL。"""
    sqls = [
        {"sql": "SELECT * FROM LOT_HISTORY l WHERE l.LOT_ID = 'L001'"},
        {"sql": "INVALID SQL !!!"},
    ]
    service = SqlAnalyzerService()
    hints = service.analyze_batch(sqls)
    # 至少有一条提示来自有效 SQL（filter 提示）
    assert len(hints) > 0


def test_analyze_confidence():
    """提示应包含置信度。"""
    sql = "SELECT AVG(YIELD_VAL) FROM WAFER_RESULT"
    service = SqlAnalyzerService()
    hints = service.analyze(sql)
    for h in hints:
        assert 0.0 <= h.confidence <= 1.0

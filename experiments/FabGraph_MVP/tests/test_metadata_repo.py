"""MetadataRepository 测试。"""
from __future__ import annotations

import pytest

from fabgraph.models.schema import ColumnSemanticType
from fabgraph.utils.exceptions import MetadataError


def test_init_db_creates_tables(metadata_repo):
    """init_db 应创建全部表。"""
    from fabgraph.repository._orm import (
        ColumnORM, ProcedureORM, SqlHistoryORM, TableORM,
    )
    with metadata_repo._session() as s:
        # 表存在即可查询
        s.query(TableORM).all()
        s.query(ColumnORM).all()
        s.query(ProcedureORM).all()
        s.query(SqlHistoryORM).all()


def test_load_from_json_idempotent(loaded_metadata_repo):
    """重复加载应幂等（清空后重写，不报主键冲突）。"""
    counts1 = loaded_metadata_repo.load_from_json()
    counts2 = loaded_metadata_repo.load_from_json()
    assert counts1 == counts2
    assert counts2["tables"] == 8
    assert counts2["columns"] > 0
    assert counts2["procedures"] == 6
    assert counts2["sql_history"] > 0


def test_get_tables(loaded_metadata_repo):
    """get_tables 返回全部表及字段。"""
    tables = loaded_metadata_repo.get_tables()
    assert len(tables) == 8
    # 每个表都有字段
    for t in tables:
        assert len(t.columns) > 0
        assert t.schema_name == "FAB"
    # 验证 LOT_HISTORY 表存在
    names = {t.table_name for t in tables}
    assert "LOT_HISTORY" in names


def test_get_table_by_name(loaded_metadata_repo):
    """按名查询表。"""
    t = loaded_metadata_repo.get_table_by_name("LOT_HISTORY")
    assert t is not None
    assert t.table_name == "LOT_HISTORY"
    assert len(t.columns) > 0
    # 不存在的表
    assert loaded_metadata_repo.get_table_by_name("NOT_EXIST") is None


def test_get_columns(loaded_metadata_repo):
    """按表查询字段。"""
    cols = loaded_metadata_repo.get_columns("LOT_HISTORY")
    assert len(cols) > 0
    # 验证字段顺序
    positions = [c.position for c in cols]
    assert positions == sorted(positions)
    # 验证 PK 字段存在
    pk_cols = [c for c in cols if c.semantic_type == ColumnSemanticType.PRIMARY_KEY]
    assert len(pk_cols) >= 1


def test_get_procedures(loaded_metadata_repo):
    """查询全部过程。"""
    procs = loaded_metadata_repo.get_procedures()
    assert len(procs) == 6
    names = {p.procedure_name for p in procs}
    assert "SP_CALC_YIELD" in names


def test_get_procedure_by_name(loaded_metadata_repo):
    """按名查询过程。"""
    p = loaded_metadata_repo.get_procedure_by_name("SP_CALC_YIELD")
    assert p is not None
    assert "LOT_HISTORY" in p.input_tables
    assert "YIELD_SUMMARY" in p.output_tables


def test_get_sql_history(loaded_metadata_repo):
    """查询 SQL 历史，含类别过滤。"""
    all_sql = loaded_metadata_repo.get_sql_history()
    assert len(all_sql) > 0
    join_sql = loaded_metadata_repo.get_sql_history(category="join")
    assert all(s["category"] == "join" for s in join_sql)
    assert len(join_sql) < len(all_sql)


def test_load_missing_json(metadata_repo, tmp_path):
    """缺失 JSON 文件应抛 MetadataError。"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(MetadataError):
        metadata_repo.load_from_json(empty_dir)


def test_column_semantic_unknown_fallback(metadata_repo):
    """semantic_type 非法值应降级为 UNKNOWN。"""
    # 直接写入一条非法 semantic_type 的字段
    from fabgraph.repository._orm import ColumnORM, TableORM
    with metadata_repo._session() as s:
        s.add(TableORM(table_name="T_BAD", schema_name="FAB"))
        s.add(ColumnORM(
            table_name="T_BAD", column_name="C1",
            semantic_type="not_a_valid_type",
        ))
        s.commit()
    cols = metadata_repo.get_columns("T_BAD")
    assert cols[0].semantic_type == ColumnSemanticType.UNKNOWN

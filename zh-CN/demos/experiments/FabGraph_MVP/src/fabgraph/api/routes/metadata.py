"""元数据路由：表/字段/过程/SQL 历史。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from fabgraph.api.deps import get_metadata_repo
from fabgraph.repository.metadata_repo import MetadataRepository

router = APIRouter()


@router.get("/tables")
async def list_tables(
    repo: MetadataRepository = Depends(get_metadata_repo),
) -> list[dict[str, Any]]:
    """返回全部表。"""
    tables = repo.get_tables()
    return [_table_summary(t) for t in tables]


@router.get("/tables/{table_name}")
async def get_table(
    table_name: str,
    repo: MetadataRepository = Depends(get_metadata_repo),
) -> dict[str, Any]:
    """返回指定表详情（含字段）。"""
    table = repo.get_table_by_name(table_name)
    if not table:
        from fabgraph.utils.exceptions import MetadataError
        raise MetadataError(f"表不存在: {table_name}")
    return _table_detail(table)


@router.get("/tables/{table_name}/columns")
async def get_columns(
    table_name: str,
    repo: MetadataRepository = Depends(get_metadata_repo),
) -> list[dict[str, Any]]:
    """返回指定表的字段列表。"""
    cols = repo.get_columns(table_name)
    return [_column_summary(c) for c in cols]


@router.get("/procedures")
async def list_procedures(
    repo: MetadataRepository = Depends(get_metadata_repo),
) -> list[dict[str, Any]]:
    """返回全部存储过程。"""
    procs = repo.get_procedures()
    return [_procedure_summary(p) for p in procs]


@router.get("/procedures/{name}")
async def get_procedure(
    name: str,
    repo: MetadataRepository = Depends(get_metadata_repo),
) -> dict[str, Any]:
    """返回指定存储过程详情。"""
    proc = repo.get_procedure_by_name(name)
    if not proc:
        from fabgraph.utils.exceptions import MetadataError
        raise MetadataError(f"过程不存在: {name}")
    return _procedure_summary(proc)


@router.get("/sql-history")
async def get_sql_history(
    category: str | None = Query(None, description="按类别过滤"),
    repo: MetadataRepository = Depends(get_metadata_repo),
) -> list[dict[str, Any]]:
    """返回历史 SQL。"""
    return repo.get_sql_history(category=category)


@router.post("/reload")
async def reload_metadata(
    repo: MetadataRepository = Depends(get_metadata_repo),
) -> dict[str, Any]:
    """从 JSON 重新加载元数据。"""
    counts = repo.load_from_json()
    return {"status": "ok", "counts": counts}


# ---------------- 序列化辅助 ----------------


def _table_summary(t) -> dict[str, Any]:
    """表摘要。"""
    return {
        "table_name": t.table_name,
        "schema_name": t.schema_name,
        "description": t.description,
        "row_count": t.row_count,
        "column_count": len(t.columns),
        "tags": list(t.tags),
    }


def _table_detail(t) -> dict[str, Any]:
    """表详情（含字段）。"""
    return {
        "table_name": t.table_name,
        "schema_name": t.schema_name,
        "description": t.description,
        "row_count": t.row_count,
        "tags": list(t.tags),
        "columns": [_column_summary(c) for c in t.columns],
    }


def _column_summary(c) -> dict[str, Any]:
    """字段摘要。"""
    return {
        "table_name": c.table_name,
        "column_name": c.column_name,
        "data_type": c.data_type,
        "nullable": c.nullable,
        "position": c.position,
        "semantic_type": c.semantic_type.value,
        "semantic_label": c.semantic_label,
        "description": c.description,
        "confidence": c.confidence,
        "aliases": list(c.aliases),
    }


def _procedure_summary(p) -> dict[str, Any]:
    """过程摘要。"""
    return {
        "procedure_name": p.procedure_name,
        "schema_name": p.schema_name,
        "description": p.description,
        "input_tables": list(p.input_tables),
        "output_tables": list(p.output_tables),
    }

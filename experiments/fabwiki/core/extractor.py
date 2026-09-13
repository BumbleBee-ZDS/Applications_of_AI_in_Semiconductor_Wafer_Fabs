"""L1 抽取：从 SQLite 数仓读取数据字典 → knowledge/raw/dictionary/{TABLE}.json。

从 sqlite_master + PRAGMA table_info 导出每张表：表名、字段、类型、主外键、
行数；外键关系读取 meta_fk 元数据表。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config
from core import db


def _dump_dict(conn, table: str) -> dict[str, Any]:
    """抽取单张表的信息为 dict。"""
    # 字段信息
    cols: list[dict[str, Any]] = []
    for row in conn.execute(f"PRAGMA table_info({table})").fetchall():
        cols.append({
            "name": row["name"],
            "type": row["type"],
            "notnull": bool(row["notnull"]),
            "default": row["dflt_value"],
            "pk": bool(row["pk"]),
        })
    pk_cols = [c["name"] for c in cols if c["pk"]]

    # 外键（来自 meta_fk 元数据表）
    fks = []
    for fk_col, src, tgt, tgt_col in db.get_meta_fk(conn):
        if src == table:
            fks.append({"column": fk_col, "references": f"{tgt}.{tgt_col}"})

    return {
        "table": table,
        "row_count": db.row_count(conn, table),
        "primary_key": pk_cols,
        "foreign_keys": fks,
        "columns": cols,
    }


def extract_all(db_path: str | Path | None = None, out_dir: str | Path | None = None) -> list[Path]:
    """一键抽取全部业务表字典，写入 raw/dictionary/。

    返回生成的 JSON 文件路径列表。
    """
    out_dir = Path(out_dir or config.RAW_DICT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = db.connect(db_path)

    written: list[Path] = []
    for table in db.table_names():
        info = _dump_dict(conn, table)
        target = out_dir / f"{table}.json"
        target.write_text(json.dumps(info, ensure_ascii=False, indent=2),
                          encoding="utf-8")
        written.append(target)
    conn.close()
    return written


def load_raw(table: str, raw_dir: str | Path | None = None) -> dict[str, Any]:
    """读取某张表已抽取的 raw JSON（供 compiler 使用）。"""
    p = Path(raw_dir or config.RAW_DICT_DIR) / f"{table}.json"
    return json.loads(p.read_text(encoding="utf-8"))
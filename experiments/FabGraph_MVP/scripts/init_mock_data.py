"""初始化模拟 Oracle 元数据。

生成高度仿真的晶圆厂元数据 JSON，输出到 data/mock_oracle/：
- tables.json / columns.json：8 张核心表，每张 20-50 字段，混合命名风格
- procedures.json：存储过程（血缘超边）
- sql_history.json：50+ 条历史 SQL（含 JOIN/别名/聚合/子查询/INSERT...SELECT）

命名风格混合（模拟历史包袱）：缩写(WFR_ID)、下划线(lot_id)、
驼峰(recipeId)、无意义编码(C001_VAL)。
数据规格常量见 mock_data_spec.py（按 300 行规范拆分）。

对应ResNet输入层：原始元数据作为特征输入，
后续由 SQL 分析器逐层提取语义（核心字段高置信，噪声字段待推断）。
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

# 确保能导入同目录的 mock_data_spec
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mock_data_spec import (  # noqa: E402
    ABBR,
    CAMEL,
    CODE,
    DTYPES,
    PROCEDURES_SPEC,
    SEM_MAP,
    SQL_HISTORY,
    TABLES_SPEC,
    UNDER,
)

random.seed(42)

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "mock_oracle"


def _gen_extra(used: set[str], count: int) -> list[tuple[str, str, str, str, float]]:
    """生成噪声字段（混合命名风格，语义未知）。

    Args:
        used: 已占用字段名集合，避免重复。
        count: 待生成数量。

    Returns:
        字段元组列表 (name, dtype, sem, label, confidence)。
    """
    pool = UNDER + CAMEL + ABBR + CODE
    out: list[tuple[str, str, str, str, float]] = []
    while len(out) < count:
        name = random.choice(pool)
        if name in used:
            name = f"{name}_{random.randint(1, 99)}"
        used.add(name)
        # 无意义编码字段多半为参数，其余未知
        sem = "param" if name.startswith(("C0", "P0")) and random.random() < 0.6 else "unk"
        out.append((name, random.choice(DTYPES), sem, "", 0.0))
    return out


def build_tables() -> tuple[list[dict], list[dict]]:
    """构建表与字段元数据。

    Returns:
        (tables, columns) 两个列表，分别写入 tables.json 与 columns.json。
    """
    tables: list[dict] = []
    columns: list[dict] = []
    for tname, spec in TABLES_SPEC.items():
        # 先将 core 字段名加入 used，避免噪声生成器产生重名
        used: set[str] = {c[0] for c in spec["core"]}
        all_cols = list(spec["core"])
        # 每表生成 12~38 个噪声字段，使总字段数落在 20~50
        all_cols += _gen_extra(used, random.randint(12, 38))

        pos = 0
        for name, dtype, sem, label, conf in all_cols:
            pos += 1
            columns.append({
                "table_name": tname, "column_name": name, "data_type": dtype,
                "nullable": sem != "pk", "position": pos,
                "semantic_type": SEM_MAP[sem], "semantic_label": label,
                "description": label, "confidence": conf, "aliases": [],
            })
        tables.append({
            "table_name": tname, "schema_name": "FAB",
            "description": spec["desc"], "row_count": random.randint(1000, 500000),
            "tags": spec["tags"],
        })
    return tables, columns


def build_procedures() -> list[dict]:
    """构建存储过程元数据（含过程体伪 SQL）。"""
    procs: list[dict] = []
    for p in PROCEDURES_SPEC:
        reads = ", ".join(p["inputs"]) or "无"
        writes = ", ".join(p["outputs"]) or "无"
        defn = (
            f"CREATE OR REPLACE PROCEDURE {p['name']} AS\n"
            f"BEGIN\n  -- 读取: {reads}; 写入: {writes}\n"
            f"  -- 业务逻辑省略（模拟）\n  NULL;\nEND;"
        )
        procs.append({
            "procedure_name": p["name"], "schema_name": "FAB",
            "definition": defn, "input_tables": p["inputs"],
            "output_tables": p["outputs"], "description": p["desc"],
        })
    return procs


def build_sql_history() -> list[dict]:
    """构建历史 SQL 列表（附 id 与类别）。"""
    return [
        {"sql_id": i + 1, "category": cat, "sql": sql}
        for i, (cat, sql) in enumerate(SQL_HISTORY)
    ]


def _write_json(path: Path, data: Any) -> None:
    """写入 JSON（UTF-8，缩进2）。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    """生成全部模拟数据并写入 data/mock_oracle/。"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tables, columns = build_tables()
    procedures = build_procedures()
    sql_history = build_sql_history()

    _write_json(OUT_DIR / "tables.json", tables)
    _write_json(OUT_DIR / "columns.json", columns)
    _write_json(OUT_DIR / "procedures.json", procedures)
    _write_json(OUT_DIR / "sql_history.json", sql_history)

    print(
        f"模拟数据生成完成 -> {OUT_DIR}\n"
        f"  表: {len(tables)}  字段: {len(columns)}  "
        f"过程: {len(procedures)}  历史SQL: {len(sql_history)}"
    )


if __name__ == "__main__":
    main()

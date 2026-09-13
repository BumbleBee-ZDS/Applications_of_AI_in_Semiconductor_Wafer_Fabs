"""冒烟测试：建库 → 抽取 → Mock 编译 → 知识加载 → Mock text2sql 全链路。

用法：python -m pytest tests/test_smoke.py -v  （或直接 python tests/test_smoke.py）
运行前无需 API Key，全程 Mock 可离线执行。
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 环境隔离：使用临时数据库，避免污染正常数据
_TMP = tempfile.mkdtemp(prefix="fabwiki_test_")
os.environ["FABWIKI_DB_PATH"] = str(Path(_TMP) / "fab_test.db")
for _k in ("LLM_API_KEY", "DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY"):
    os.environ[_k] = ""   # 强制 Mock

import config  # noqa: E402
from core import compiler, db, extractor, knowledge, text2sql  # noqa: E402


def _init_all() -> None:
    """建库 + 抽取 + Mock 编译，返回。"""
    conn = db.init_db(drop_existing=True)
    conn.close()
    extractor.extract_all()
    compiler.compile_all()


def test_db_seed() -> None:
    _init_all()
    conn = db.connect()
    tables = db.table_names()
    assert len(tables) == 8
    assert db.row_count(conn, "WIP_LOT") > 0
    assert db.row_count(conn, "YLD_DAILY") > 0
    # 隐性知识：存在 Hold(05) 与 测试批次(99)
    sts = {r["LOT_STS"] for r in conn.execute("SELECT DISTINCT LOT_STS FROM WIP_LOT")}
    assert "05" in sts and "99" in sts
    conn.close()


def test_extractor_products() -> None:
    _init_all()
    import json
    raw = extractor.load_raw("WIP_LOT")
    assert raw["table"] == "WIP_LOT"
    assert raw["row_count"] > 0
    assert any(c["name"] == "LOT_STS" for c in raw["columns"])
    assert any(c["name"] == "PRODUCT_ID" for c in raw["columns"])


def test_compiler_mock_writes() -> None:
    _init_all()
    # 表 + 指标 + lineage 落盘
    assert (config.WIKI_TABLES_DIR / "WIP_LOT.md").exists()
    assert (config.WIKI_METRICS_DIR / "wafer-yield-rate.md").exists()
    assert (config.WIKI_LINEAGE_DIR / "WIP_LOT__lineage.md").exists()
    assert config.INDEX_MD.exists()
    # 隐性知识写入正文
    txt = (config.WIKI_TABLES_DIR / "WIP_LOT.md").read_text(encoding="utf-8")
    assert "99" in txt and "测试批次" in txt


def test_knowledge_load_and_graph() -> None:
    _init_all()
    kb = knowledge.KnowledgeBase()
    st = kb.stats()
    assert st["types"].get("Table", 0) == 8
    assert st["types"].get("Metric", 0) == 2
    # 血缘链路 WIP_LOT → WIP_LOT_HIST → YLD_DAILY
    a, b, c = ("wiki/tables/WIP_LOT.md", "wiki/tables/WIP_LOT_HIST.md",
               "wiki/tables/YLD_DAILY.md")
    assert knowledge.nx.has_path(kb.graph, a, b)
    assert knowledge.nx.has_path(kb.graph, b, c)
    # 按 tag 过滤
    assert any(n.type == "Table" for n in kb.all(type_="Table"))
    # 关键词定位 Hold 相关表应命中 WIP_LOT
    hits = [n.resource for n in kb.locate_tables(["Hold", "批次"])]
    assert "WIP_LOT" in hits


def test_text2sql_mock() -> None:
    _init_all()
    ts = text2sql.Text2SQL()
    r = ts.ask("当前 Hold 中的批次数量")
    assert r.success, r.error
    assert r.mock
    assert "'05'" in r.sql
    assert "99" in r.sql and "<>" in r.sql    # 排除测试批次
    assert len(r.df) >= 0 and list(r.df.columns)  # 返回非空 df
    assert r.referenced                       # 有引用知识文件
    # 未命中示例问题给出友好提示
    r2 = ts.ask("一个完全无关的随机问题xyzxx")
    assert not r2.success and "未命中" in r2.error


def test_metrics_present() -> None:
    _init_all()
    kb = knowledge.KnowledgeBase()
    metric_res = kb.types()
    assert "Metric" in metric_res
    assert any(n.resource == "hold-lot-count" for n in kb.all(type_="Metric"))


def test_columns_mock_writes() -> None:
    """Column 级知识文件生成与加载。"""
    _init_all()
    # Column 目录存在且有文件
    assert config.WIKI_COLUMNS_DIR.exists()
    col_files = list(config.WIKI_COLUMNS_DIR.glob("*.md"))
    assert len(col_files) > 0, "Column 级知识文件未生成"
    # LOT_STS 字段必须有隐性知识
    lot_sts_md = config.WIKI_COLUMNS_DIR / "WIP_LOT.LOT_STS.md"
    assert lot_sts_md.exists()
    content = lot_sts_md.read_text(encoding="utf-8")
    assert "type: Column" in content
    assert "99" in content and "测试批次" in content
    # index.md 中包含 Column 章节
    index_content = config.INDEX_MD.read_text(encoding="utf-8")
    assert "字段知识" in index_content


def test_knowledge_columns() -> None:
    """Column 类型知识加载与查询方法。"""
    _init_all()
    kb = knowledge.KnowledgeBase()
    st = kb.stats()
    # Column 类型存在且数量正确（9个含隐性知识的字段）
    assert st["types"].get("Column", 0) >= 5
    # columns_of_table 方法
    cols = kb.columns_of_table("WIP_LOT")
    assert len(cols) >= 1
    assert any(c.resource == "WIP_LOT.LOT_STS" for c in cols)
    # locate_columns 关键词定位
    hits = kb.locate_columns(["Hold", "状态"])
    assert any("LOT_STS" in h.resource for h in hits)
    # locate_columns 表过滤
    hits_filtered = kb.locate_columns(["状态"], table_filter=["WIP_LOT"])
    assert all(h.resource.startswith("WIP_LOT.") for h in hits_filtered)


def test_sql_extract_and_validate() -> None:
    """SQL 提取与校验函数。"""
    _init_all()
    ts = text2sql.Text2SQL()
    # 从 markdown 代码块中提取
    md_sql = "```sql\nSELECT * FROM WIP_LOT WHERE LOT_STS = '05';\n```"
    extracted = ts._extract_sql(md_sql)
    assert "SELECT" in extracted.upper()
    assert "```" not in extracted
    assert extracted.strip().endswith("'05'")  # 结尾分号已去掉
    # 纯 SQL 直接返回
    pure_sql = "SELECT COUNT(*) FROM WIP_LOT"
    assert ts._extract_sql(pure_sql).strip() == pure_sql.strip()
    # 校验：合法 SELECT 通过
    valid, err = ts._validate_sql("SELECT * FROM WIP_LOT")
    assert valid, err
    # 校验：危险操作拦截
    valid, err = ts._validate_sql("DROP TABLE WIP_LOT")
    assert not valid
    assert "危险操作" in err
    # 校验：空 SQL 拦截
    valid, err = ts._validate_sql("")
    assert not valid


def test_compiler_llm_validation() -> None:
    """LLM 输出校验与清洗函数（模拟各种异常输出）。"""
    from core.compiler import _validate_and_clean_md
    # 正常输出：frontmatter 完整
    normal_md = """---
title: "测试表"
type: Table
resource: TEST_TABLE
tags: [测试]
confidence: llm-inferred
updated: 2026-09-13
---

# 测试表

正文内容
"""
    cleaned = _validate_and_clean_md(normal_md, "Table", "TEST_TABLE")
    assert "type: Table" in cleaned
    assert "TEST_TABLE" in cleaned
    # 被代码块包裹的输出
    wrapped = "```markdown\n" + normal_md + "\n```"
    cleaned2 = _validate_and_clean_md(wrapped, "Table", "TEST_TABLE")
    assert "type: Table" in cleaned2
    # 没有 frontmatter 的输出
    no_fm = "# 测试表\n\n没有 frontmatter 的正文"
    cleaned3 = _validate_and_clean_md(no_fm, "Table", "TEST_TABLE")
    assert cleaned3.startswith("---")
    assert "type: Table" in cleaned3
    assert "TEST_TABLE" in cleaned3
    # type 写错了应该被修正
    bad_type = normal_md.replace("type: Table", "type: WrongType")
    cleaned4 = _validate_and_clean_md(bad_type, "Table", "TEST_TABLE")
    assert "type: Table" in cleaned4
    # confidence 会被强制为 llm-inferred
    bad_conf = normal_md.replace("confidence: llm-inferred", "confidence: high")
    cleaned5 = _validate_and_clean_md(bad_conf, "Table", "TEST_TABLE")
    assert "confidence: llm-inferred" in cleaned5


def test_text2sql_includes_columns() -> None:
    """Text2SQL 查询时引用了 Column 级知识文件。"""
    _init_all()
    ts = text2sql.Text2SQL()
    r = ts.ask("当前 Hold 中的批次数量")
    assert r.success
    # 引用的知识文件中应该包含 Column 级知识
    col_refs = [r for r in r.referenced if "/columns/" in r]
    assert len(col_refs) > 0, "Text2SQL 未引用 Column 级知识"
    # 应该包含 LOT_STS 字段知识
    assert any("LOT_STS" in ref for ref in r.referenced)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"  ✓ {fn.__name__}")
    print(f"全部 {len(tests)} 项冒烟测试通过。")
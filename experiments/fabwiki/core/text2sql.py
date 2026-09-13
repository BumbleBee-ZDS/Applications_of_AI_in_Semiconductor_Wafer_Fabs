"""知识导航式 Text2SQL：定位知识 → 确定性读取 → 组装 prompt → 生成 SQL → 执行。

与朴素 Text2SQL 的本质区别（必须实现）：
1. 用户问题 → 关键词/LLM 从知识索引定位相关的 2~5 张表知识点；
2. **确定性读取**这些表知识点的完整 markdown（含隐性知识、Text2SQL 注意事项）
   + spec/text2sql-rules.md，而不是向量分块检索；
3. 组装 prompt（问题 + 知识全文 + 规则 + few-shot）→ LLM 生成 SQL；
4. 在 SQLite 执行，返回 DataFrame + 生成的 SQL + 引用的知识文件列表；
5. 失败重试一次（把报错信息回填给 LLM）。

Mock 模式（无 Key）：内置 5 个示例问题 → 预写 SQL 的映射（问题做模糊匹配）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

import config
from core import db, knowledge
from core.llm import chat_complete


@dataclass
class Text2SQLResult:
    question: str
    sql: str
    df: pd.DataFrame
    referenced: list[str]          # 引用的知识文件（相对 knowledge/ 路径）
    logs: list[str] = field(default_factory=list)
    mock: bool = False
    error: str = ""

    @property
    def success(self) -> bool:
        return self.error == ""


class Text2SQL:
    """知识导航式 Text2SQL 引擎。"""

    def __init__(self, db_path: str | Path | None = None,
                 kb: knowledge.KnowledgeBase | None = None) -> None:
        self.db_path = Path(db_path or str(config.get_db_path()))
        self.kb = kb or knowledge.KnowledgeBase()
        self._rules = self._read_rules()
        self._mock_map = self._build_mock_map()

    # ------------------------------------------------------------------
    # 知识读取
    # ------------------------------------------------------------------
    def _read_rules(self) -> str:
        p = config.SPEC_DIR / "text2sql-rules.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def _table_full_text(self, node: knowledge.KnowledgeNode) -> str:
        """确定性读取某表知识点的完整 markdown（frontmatter + 正文）。"""
        fm = node.frontmatter
        fm_block = "\n".join(f"{k}: {v}" for k, v in fm.items())
        return f"---\n{fm_block}\n---\n\n{node.body}"

    def _column_full_text(self, node: knowledge.KnowledgeNode) -> str:
        """确定性读取某字段知识点的完整 markdown。"""
        fm = node.frontmatter
        fm_block = "\n".join(f"{k}: {v}" for k, v in fm.items())
        return f"---\n{fm_block}\n---\n\n{node.body}"

    def locate(self, question: str) -> list[knowledge.KnowledgeNode]:
        """第 1 步：从问题抽取关键词，定位相关表知识点（2~5 张）。"""
        keywords = self._keywords(question)
        nodes = self.kb.locate_tables(keywords)
        return nodes[:5]

    def locate_columns_for_tables(self, question: str,
                                   table_nodes: list[knowledge.KnowledgeNode]) -> list[knowledge.KnowledgeNode]:
        """第 1b 步：为定位到的表找相关的字段知识点（含隐性知识的字段）。"""
        keywords = self._keywords(question)
        table_names = [n.resource for n in table_nodes]
        # 优先：问题关键词命中的字段
        col_nodes = self.kb.locate_columns(keywords, table_filter=table_names)
        # 补充：这些表的所有含隐性知识的字段（保证不遗漏）
        for tbl in table_names:
            for c in self.kb.columns_of_table(tbl):
                if c.path not in [n.path for n in col_nodes]:
                    col_nodes.append(c)
        return col_nodes

    @staticmethod
    def _keywords(q: str) -> list[str]:
        """从中文问题粗略抽取候选关键词。"""
        # 常见业务词先保留，再按字词拆分
        hits = re.findall(r"[A-Za-z_]{2,}", q)   # 英文表名/字段线索
        tokens = re.sub(r"[\W_]+", " ", q)
        cn = [t for t in tokens.split() if len(t) >= 2]
        return list(dict.fromkeys(hits + cn))

    # ------------------------------------------------------------------
    # Mock 映射
    # ------------------------------------------------------------------
    def _build_mock_map(self) -> list[tuple[str, str, str]]:
        """Mock 模式示例：[(匹配关键词, SQL, 描述)]，问题做模糊匹配。"""
        return [
            ("hold 批次", (
                "SELECT LOT_ID, PRODUCT_ID, STAGE_CD, LOT_STS, LAST_MOD_DT\n"
                "FROM WIP_LOT\n"
                "WHERE LOT_STS = '05'\n"
                "  AND LOT_STS <> '99'\n"
                "ORDER BY LAST_MOD_DT DESC;"),
             "当前 Hold 中的批次（排除测试批次）"),
            ("良率 趋势", (
                "SELECT STAT_DT, PRODUCT_ID, AVG(YLD_RATE) AS AVG_YLD\n"
                "FROM YLD_DAILY\n"
                "WHERE STAT_DT >= date('now', '-1 month')\n"
                "GROUP BY STAT_DT, PRODUCT_ID\n"
                "ORDER BY STAT_DT;"),
             "最近一个月各产品良率趋势"),
            ("缺陷 top", (
                "SELECT S.STEP_NM, S.STEP_GRP, SUM(D.DEFECT_CNT) AS TOTAL_DEFECT\n"
                "FROM QCS_DEFECT D\n"
                "JOIN ENG_STEP S ON D.STEP_ID = S.STEP_ID\n"
                "WHERE S.STEP_GRP = 'PHOTO'\n"
                "GROUP BY S.STEP_NM, S.STEP_GRP\n"
                "ORDER BY TOTAL_DEFECT DESC\n"
                "LIMIT 10;"),
             "PHOTO 工序缺陷 Top10"),
            ("设备 可用", (
                "SELECT EQP_TYPE, STATUS_CD, COUNT(*) AS CNT\n"
                "FROM EQP_EQUIPMENT\n"
                "WHERE STATUS_CD IN ('R', 'I', 'M')\n"
                "GROUP BY EQP_TYPE, STATUS_CD\n"
                "ORDER BY EQP_TYPE, STATUS_CD;"),
             "各类型可用设备（R/I/M）数量"),
            ("在制品 数量", (
                "SELECT PRODUCT_ID, COUNT(*) AS LOT_CNT\n"
                "FROM WIP_LOT\n"
                "WHERE LOT_STS <> '99'\n"
                "GROUP BY PRODUCT_ID\n"
                "ORDER BY LOT_CNT DESC;"),
             "各产品在制品批次数量（排除测试批次）"),
        ]

    def _match_mock(self, q: str) -> tuple[str, str, str | None]:
        """模糊匹配示例问题；命中返回 (sql, 描述, None)，未命中返回 ("","",提示)。"""
        ql = q.lower()
        best: tuple[int, str, str] | None = None   # (权重, sql, 描述)
        for key, sql, desc in self._mock_map:
            k_tokens = re.findall(r"[a-z0-9\u4e00-\u9fff]+", key.lower())
            if k_tokens and all(t in ql for t in k_tokens):
                w = len(k_tokens)
                if best is None or w > best[0]:
                    best = (w, sql, desc)
        if best is None:
            return "", "", "未命中内置示例，请用相近问题重试或配置 API Key 走真实 LLM。"
        return best[1], best[2], None

    # ------------------------------------------------------------------
    # SQL 提取与校验
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_sql(text: str) -> str:
        """从 LLM 输出中提取纯 SQL。

        处理情况：
        - 被 ```sql``` 或 ```markdown``` 包裹
        - 前后有解释性文字
        - 多条 SQL 取第一条
        """
        if not text:
            return ""
        sql = text.strip()
        # 去除 markdown 代码块
        import re as _re
        # 匹配 ```sql ... ``` 或 ``` ... ```
        code_block = _re.search(r"```(?:sql|markdown)?\s*\n?(.*?)\n?```", sql, _re.DOTALL | _re.IGNORECASE)
        if code_block:
            sql = code_block.group(1).strip()
        # 如果有多条语句，取第一条（以分号分隔，但要注意字符串内的分号）
        # 简单处理：找第一个不在引号内的分号
        # 先尝试用 ;\n 或 ;\s*-- 等明显分隔
        lines = sql.split("\n")
        clean_lines = []
        for line in lines:
            # 跳过纯注释行
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            clean_lines.append(line)
        sql = "\n".join(clean_lines).strip()
        # 去除结尾分号
        sql = sql.rstrip(";").strip()
        return sql

    @staticmethod
    def _validate_sql(sql: str) -> tuple[bool, str]:
        """简单校验 SQL 合法性（语法层面轻量检查）。

        返回 (是否通过, 问题描述)
        """
        if not sql:
            return False, "SQL 为空"
        # 先检查是否有危险操作（安全第一）
        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        for kw in dangerous:
            if re.search(r"(?:^|\s)" + kw + r"\s", sql, re.IGNORECASE):
                return False, f"包含危险操作：{kw}（仅允许 SELECT 查询）"
        # 基本检查：必须包含 SELECT
        if not re.search(r"\bSELECT\b", sql, re.IGNORECASE):
            return False, "SQL 中未找到 SELECT 语句"
        return True, ""

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def ask(self, question: str) -> Text2SQLResult:
        """知识导航 Text2SQL 主入口。"""
        logs: list[str] = []
        nodes = self.locate(question)
        referenced = []
        ctx = []
        # 确定性读取相关表知识全文（第 2 步）
        for n in nodes:
            referenced.append(str(n.path))
            ctx.append(f"===== 知识文件：{n.path} =====\n{n.resource}\n{self._table_full_text(n)}")

        # 确定性读取相关字段知识全文（第 2b 步：Column 级隐性知识）
        col_nodes = self.locate_columns_for_tables(question, nodes)
        for c in col_nodes:
            referenced.append(str(c.path))
            ctx.append(f"===== 字段知识：{c.path} =====\n{c.resource}\n{self._column_full_text(c)}")

        ctx_text = "\n\n".join(ctx)
        logs.append(f"定位相关表：{len(nodes)} 张 -> {[n.resource for n in nodes]}")
        if col_nodes:
            logs.append(f"相关字段知识：{len(col_nodes)} 个 -> {[c.resource for c in col_nodes]}")

        # Mock 模式：直接匹配内置示例
        if not config.LLM_AVAILABLE:
            sql, desc, missed = self._match_mock(question)
            if missed:
                return Text2SQLResult(question, "", pd.DataFrame(),
                                      referenced, logs, mock=True, error=missed)
            logs.append(f"[Mock] 命中示例：{desc}")
            return self._execute(question, sql, referenced, logs, mock=True)

        # 真实 LLM：组装 prompt（第 3 步）
        sql = self._llm_generate(question, ctx_text, referenced, logs)
        if not sql:
            return Text2SQLResult(question, "", pd.DataFrame(),
                                  referenced, logs, mock=False,
                                  error="LLM 未生成 SQL（已降级）。")
        return self._execute(question, sql, referenced, logs, mock=False)

    def _llm_generate(self, question: str, ctx: str, referenced: list[str],
                      logs: list[str]) -> str:
        system = ("你是半导体晶圆厂数据仓库的 Text2SQL 专家。仅根据给定的知识文件"
                  "和规则生成一条 SQLite 可执行的 SQL。只输出 SQL 本身，不要解释，"
                  "不要用 markdown 代码块包裹，不要结尾分号。")
        user = (
            f"用户问题：{question}\n\n"
            f"相关表知识全文：\n{ctx}\n\n"
            f"生成规则（few-shot 等）：\n{self._rules}\n\n"
            f"请生成 SQL。"
        )
        raw = chat_complete(system, user) or ""
        sql = self._extract_sql(raw)
        valid, err = self._validate_sql(sql)
        if not valid:
            logs.append(f"[SQL 校验] {err}，原始输出：{raw[:100]}...")
            return ""
        logs.append("[LLM] SQL 生成成功")
        return sql

    def _execute(self, question: str, sql: str, referenced: list[str],
                 logs: list[str], mock: bool) -> Text2SQLResult:
        """执行 SQL，失败重试一次（把报错回填给 LLM）。"""
        conn = db.connect(self.db_path)
        try:
            df = pd.read_sql_query(sql, conn)
            return Text2SQLResult(question, sql, df, referenced, logs, mock=mock)
        except Exception as e1:
            logs.append(f"[执行失败] {e1}")
            if not mock and config.LLM_AVAILABLE:
                # 重试：把报错信息回填给 LLM（第 5 步）
                retry_sql = self._retry_sql(question, sql, referenced, str(e1), logs)
                if retry_sql:
                    try:
                        df = pd.read_sql_query(retry_sql, conn)
                        logs.append("[重试] 修正后执行成功")
                        return Text2SQLResult(question, retry_sql, df, referenced,
                                              logs, mock=False)
                    except Exception as e2:
                        logs.append(f"[重试失败] {e2}")
            return Text2SQLResult(question, sql, pd.DataFrame(), referenced,
                                  logs, mock=mock, error=str(e1))
        finally:
            conn.close()

    def _retry_sql(self, question: str, sql: str, referenced: list[str],
                   err: str, logs: list[str]) -> str:
        sys = ("你是 SQL 修复专家。根据报错信息修正 SQL，使其在 SQLite 可执行。"
               "只输出修正后的 SQL 本身。")
        usr = (f"用户问题：{question}\n原 SQL：\n{sql}\n\n"
               f"执行报错：\n{err}\n\n请修正 SQL。")
        raw = chat_complete(sys, usr) or ""
        fixed = self._extract_sql(raw)
        valid, _ = self._validate_sql(fixed)
        if valid and fixed.lower() != sql.lower():
            return fixed
        return ""
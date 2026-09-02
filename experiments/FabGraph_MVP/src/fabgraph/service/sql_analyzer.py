"""SQL 语义分析服务。

将 :class:`ParsedSQL` 结构化信息转换为 :class:`SemanticHint` 列表，
为 Schema Graph 注入 join_inferred / filter / aggregate / alias / lineage 信号。

对应ResNet残差块：每条历史 SQL 贡献增量语义信号，
叠加到字段的语义推断结果上，缓解长链推断的梯度衰减。
"""
from __future__ import annotations

import logging
from typing import Iterable

from fabgraph.models.schema import SemanticHint
from fabgraph.repository.metadata_repo import MetadataRepository
from fabgraph.utils.exceptions import SQLAnalysisError
from fabgraph.utils.sql_parser import ParsedSQL, SqlParser, TableRef

logger = logging.getLogger(__name__)

# 聚合函数 -> 语义提示类型
_AGG_HINT_TYPE = "aggregate"


class SqlAnalyzerService:
    """SQL 语义分析器。

    Attributes:
        parser: SQL 解析器。
        metadata_repo: 元数据仓储（用于别名解析与表名校验）。
    """

    def __init__(
        self,
        parser: SqlParser | None = None,
        metadata_repo: MetadataRepository | None = None,
    ) -> None:
        """初始化分析器。

        Args:
            parser: SQL 解析器，默认新建。
            metadata_repo: 元数据仓储（可选，用于增强解析）。
        """
        self.parser = parser or SqlParser()
        self.metadata_repo = metadata_repo
        self._alias_to_table: dict[str, str] = {}

    def analyze(self, sql: str) -> list[SemanticHint]:
        """分析单条 SQL，提取语义提示。

        Args:
            sql: SQL 文本。

        Returns:
            :class:`SemanticHint` 列表。
        """
        parsed = self.parser.parse(sql)
        self._alias_to_table = {t.alias: t.name for t in parsed.tables}
        hints: list[SemanticHint] = []
        hints.extend(self._extract_join_hints(parsed))
        hints.extend(self._extract_filter_hints(parsed))
        hints.extend(self._extract_aggregate_hints(parsed))
        hints.extend(self._extract_alias_hints(parsed))
        hints.extend(self._extract_lineage_hints(parsed))
        logger.debug("SQL 分析完成: %d 条提示 (sql_len=%d)", len(hints), len(sql))
        return hints

    def analyze_batch(
        self, sqls: Iterable[dict]
    ) -> list[SemanticHint]:
        """批量分析 SQL 历史，聚合语义提示。

        Args:
            sqls: SQL 字典列表，每项含 ``sql`` 字段。

        Returns:
            全部 :class:`SemanticHint` 列表。
        """
        all_hints: list[SemanticHint] = []
        for item in sqls:
            sql = item.get("sql", "") if isinstance(item, dict) else str(item)
            if not sql:
                continue
            try:
                hints = self.analyze(sql)
                all_hints.extend(hints)
            except SQLAnalysisError as e:
                logger.warning("跳过无法解析的 SQL: %s", e)
        logger.info("批量分析完成: 共 %d 条提示", len(all_hints))
        return all_hints

    # ---------------- 提示提取 ----------------

    def _extract_join_hints(self, parsed: ParsedSQL) -> list[SemanticHint]:
        """提取 join_key 提示。

        每条 JOIN 条件生成一个 join_key 提示：
        - 本地字段 = join 条件左侧
        - hint_value = 右侧字段的 ``TABLE.COLUMN`` 形式
        """
        hints: list[SemanticHint] = []
        for join in parsed.joins:
            if not join.left_table or not join.right_table:
                continue
            left_ref = f"{join.left_table}.{join.left_column}"
            right_ref = f"{join.right_table}.{join.right_column}"
            # 双向各生成一条（便于双向 JOIN 边）
            hints.append(SemanticHint(
                table_name=join.left_table, column_name=join.left_column,
                hint_type="join_key", hint_value=right_ref,
                confidence=0.85, source_sql="", inferred_by_llm=False,
            ))
            hints.append(SemanticHint(
                table_name=join.right_table, column_name=join.right_column,
                hint_type="join_key", hint_value=left_ref,
                confidence=0.85, source_sql="", inferred_by_llm=False,
            ))
        return hints

    def _extract_filter_hints(self, parsed: ParsedSQL) -> list[SemanticHint]:
        """提取 filter 提示。

        从 WHERE 条件中识别字段过滤，生成 filter 提示。
        """
        hints: list[SemanticHint] = []
        for filt in parsed.filters:
            # 简单解析 "TABLE.COLUMN = value" 形式
            for table_ref in parsed.tables:
                # 在 filter 文本中查找该表别名/字段
                hint = self._parse_filter_condition(filt, table_ref)
                if hint:
                    hints.append(hint)
        return hints

    def _parse_filter_condition(
        self, filt: str, table_ref: TableRef
    ) -> SemanticHint | None:
        """解析单条过滤条件，匹配表字段。

        启发式：过滤条件中若出现 ``alias.column`` 或表名，则生成提示。
        """
        upper = filt.upper()
        # 查找 alias. 形式
        prefix = f"{table_ref.alias}."
        if prefix in upper:
            # 提取字段名
            idx = upper.index(prefix) + len(prefix)
            rest = upper[idx:]
            col_name = ""
            for ch in rest:
                if ch.isalnum() or ch == "_":
                    col_name += ch
                else:
                    break
            if col_name:
                return SemanticHint(
                    table_name=table_ref.name, column_name=col_name,
                    hint_type="filter", hint_value=filt,
                    confidence=0.7, source_sql="", inferred_by_llm=False,
                )
        return None

    def _extract_aggregate_hints(self, parsed: ParsedSQL) -> list[SemanticHint]:
        """提取 aggregate 提示。"""
        hints: list[SemanticHint] = []
        for agg in parsed.aggregations:
            col = agg.get("column", "")
            func = agg.get("func", "")
            if not col or col == "*":
                continue
            # 字段所属表：尝试从 columns 中找
            table_name = self._find_table_of_column(parsed, col)
            if not table_name:
                continue
            hints.append(SemanticHint(
                table_name=table_name, column_name=col,
                hint_type=_AGG_HINT_TYPE, hint_value=func,
                confidence=0.8, source_sql="", inferred_by_llm=False,
                extra={"alias": agg.get("alias", "")},
            ))
        return hints

    def _find_table_of_column(self, parsed: ParsedSQL, column_name: str) -> str:
        """从 ParsedSQL 中查找字段所属表名。"""
        upper = column_name.upper()
        for col in parsed.columns:
            if col.name != upper:
                continue
            if col.table_alias:
                return self._alias_to_table.get(col.table_alias, col.table_alias)
            # 无别名时取第一个表（启发式）
            if parsed.tables:
                return parsed.tables[0].name
        return ""

    def _extract_alias_hints(self, parsed: ParsedSQL) -> list[SemanticHint]:
        """提取 alias 提示（SQL 中表的短别名）。"""
        hints: list[SemanticHint] = []
        for table_ref in parsed.tables:
            if table_ref.alias and table_ref.alias != table_ref.name:
                # 别名提示：表级别的字段别名
                hints.append(SemanticHint(
                    table_name=table_ref.name, column_name="*",
                    hint_type="alias", hint_value=table_ref.alias,
                    confidence=0.6, source_sql="", inferred_by_llm=False,
                ))
        return hints

    def _extract_lineage_hints(self, parsed: ParsedSQL) -> list[SemanticHint]:
        """提取 lineage 提示（INSERT...SELECT 场景）。

        当 SQL 为 INSERT 且有 target_table 时，生成 lineage 提示。
        """
        hints: list[SemanticHint] = []
        if parsed.category != "insert" or not parsed.target_table:
            return hints
        for table_ref in parsed.tables:
            if table_ref.name == parsed.target_table:
                continue
            hints.append(SemanticHint(
                table_name=table_ref.name, column_name="*",
                hint_type="lineage", hint_value=parsed.target_table,
                confidence=0.9, source_sql="", inferred_by_llm=False,
            ))
        return hints

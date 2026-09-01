"""SQL 解析器（基于 sqlglot）。

从 SQL 文本中提取结构化信息：
- 涉及的表（含别名）
- 字段引用（含所属表别名）
- JOIN 条件（左字段、右字段、连接类型）
- WHERE 过滤条件
- 聚合函数（SUM/COUNT/AVG/MIN/MAX）
- INSERT/CREATE 目标表（血缘用）

对应ResNet特征提取卷积：从原始 SQL 文本中逐层抽取
表/字段/JOIN/聚合等离散特征，供 sql_analyzer 注入语义。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from fabgraph.utils.exceptions import SQLAnalysisError

logger = logging.getLogger(__name__)


@dataclass
class TableRef:
    """表引用。

    Attributes:
        name: 表名（大写）。
        alias: 别名（无则等于 name）。
    """

    name: str
    alias: str = ""


@dataclass
class ColumnRef:
    """字段引用。

    Attributes:
        name: 字段名（大写）。
        table_alias: 所属表别名/表名（可能为空）。
    """

    name: str
    table_alias: str = ""


@dataclass
class JoinCondition:
    """JOIN 条件。

    Attributes:
        left_table: 左表名。
        left_column: 左字段名。
        right_table: 右表名。
        right_column: 右字段名。
        join_type: 连接类型（INNER/LEFT/RIGHT/FULL）。
    """

    left_table: str
    left_column: str
    right_table: str
    right_column: str
    join_type: str = "INNER"


@dataclass
class ParsedSQL:
    """SQL 解析结果。

    Attributes:
        tables: 涉及的表引用。
        columns: 引用的字段。
        joins: JOIN 条件列表。
        filters: WHERE 过滤条件（原始表达式文本）。
        aggregations: 聚合函数调用 [{func, column, alias}]。
        target_table: INSERT/CREATE 目标表（无则空）。
        category: SQL 类别（select/insert/create/update/delete）。
    """

    tables: list[TableRef] = field(default_factory=list)
    columns: list[ColumnRef] = field(default_factory=list)
    joins: list[JoinCondition] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    aggregations: list[dict[str, str]] = field(default_factory=list)
    target_table: str = ""
    category: str = "select"


class SqlParser:
    """SQL 解析器（sqlglot 包装）。"""

    def parse(self, sql: str, dialect: str = "oracle") -> ParsedSQL:
        """解析 SQL 文本。

        Args:
            sql: SQL 文本。
            dialect: sqlglot 方言，默认 oracle。

        Returns:
            :class:`ParsedSQL` 解析结果。

        Raises:
            SQLAnalysisError: 解析失败。
        """
        try:
            statements = sqlglot.parse(sql, read=dialect)
        except ParseError as e:
            raise SQLAnalysisError(f"SQL 解析失败: {e}") from e
        if not statements or statements[0] is None:
            return ParsedSQL()
        # 取第一条语句（多语句时仅解析首条）
        stmt = statements[0]
        return self._extract(stmt)

    def _extract(self, stmt: exp.Expression) -> ParsedSQL:
        """从 AST 提取结构化信息。"""
        result = ParsedSQL()
        result.category = self._infer_category(stmt)
        # 目标表（INSERT/CREATE）
        result.target_table = self._extract_target_table(stmt)
        # 表与别名
        result.tables = self._extract_tables(stmt)
        # JOIN 条件
        result.joins = self._extract_joins(stmt, result.tables)
        # 字段引用
        result.columns = self._extract_columns(stmt)
        # WHERE 过滤
        result.filters = self._extract_filters(stmt)
        # 聚合函数
        result.aggregations = self._extract_aggregations(stmt)
        return result

    @staticmethod
    def _infer_category(stmt: exp.Expression) -> str:
        """推断 SQL 类别。"""
        key = type(stmt).__name__.upper()
        mapping = {
            "SELECT": "select", "INSERT": "insert", "CREATE": "create",
            "UPDATE": "update", "DELETE": "delete",
        }
        return mapping.get(key, "select")

    def _extract_target_table(self, stmt: exp.Expression) -> str:
        """提取 INSERT/CREATE 目标表。"""
        if isinstance(stmt, exp.Insert):
            target = stmt.find(exp.Table)
            if target and target.name:
                return target.name.upper()
        if isinstance(stmt, exp.Create):
            target = stmt.find(exp.Table)
            if target and target.name:
                return target.name.upper()
        return ""

    def _extract_tables(self, stmt: exp.Expression) -> list[TableRef]:
        """提取全部表引用（含别名）。"""
        tables: list[TableRef] = []
        seen: set[str] = set()
        for tbl in stmt.find_all(exp.Table):
            name = tbl.name.upper()
            if not name or name in seen:
                continue
            alias = tbl.alias or name
            tables.append(TableRef(name=name, alias=alias.upper()))
            seen.add(name)
        return tables

    def _extract_joins(
        self, stmt: exp.Expression, tables: list[TableRef]
    ) -> list[JoinCondition]:
        """提取 JOIN 条件。"""
        joins: list[JoinCondition] = []
        alias_to_name = {t.alias: t.name for t in tables}
        for join in stmt.find_all(exp.Join):
            join_type = self._join_kind(join)
            on = join.args.get("on")
            if not on:
                continue
            # ON 条件通常是 eq(left, right)
            for eq in on.find_all(exp.EQ):
                cols = list(eq.find_all(exp.Column))
                if len(cols) < 2:
                    continue
                left, right = cols[0], cols[1]
                joins.append(JoinCondition(
                    left_table=self._resolve_table(left, alias_to_name),
                    left_column=left.name.upper(),
                    right_table=self._resolve_table(right, alias_to_name),
                    right_column=right.name.upper(),
                    join_type=join_type,
                ))
        return joins

    @staticmethod
    def _join_kind(join: exp.Join) -> str:
        """获取 JOIN 类型。"""
        kind = join.args.get("kind") or join.args.get("side") or "INNER"
        return str(kind).upper() if kind else "INNER"

    @staticmethod
    def _resolve_table(col: exp.Column, alias_map: dict[str, str]) -> str:
        """根据字段所属别名解析真实表名。"""
        tbl = col.table
        if tbl:
            return alias_map.get(tbl.upper(), tbl.upper())
        return ""

    def _extract_columns(self, stmt: exp.Expression) -> list[ColumnRef]:
        """提取字段引用（去重）。"""
        cols: list[ColumnRef] = []
        seen: set[tuple[str, str]] = set()
        for col in stmt.find_all(exp.Column):
            name = col.name.upper()
            if not name:
                continue
            tbl = col.table.upper() if col.table else ""
            key = (name, tbl)
            if key in seen:
                continue
            cols.append(ColumnRef(name=name, table_alias=tbl))
            seen.add(key)
        return cols

    def _extract_filters(self, stmt: exp.Expression) -> list[str]:
        """提取 WHERE 条件（原始表达式文本）。"""
        filters: list[str] = []
        where = stmt.find(exp.Where)
        if not where:
            return filters
        # 取顶层 AND 分隔的条件
        for cond in self._split_and(where.this):
            filters.append(cond.sql())
        return filters

    @staticmethod
    def _split_and(expr: exp.Expression) -> list[exp.Expression]:
        """将 AND 链拆分为条件列表。"""
        if isinstance(expr, exp.And):
            return SqlParser._split_and(expr.left) + SqlParser._split_and(expr.right)
        return [expr] if expr else []

    def _extract_aggregations(self, stmt: exp.Expression) -> list[dict[str, str]]:
        """提取聚合函数调用。"""
        aggs: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        agg_classes = (exp.Sum, exp.Count, exp.Avg, exp.Min, exp.Max)
        for node in stmt.find_all(*agg_classes):
            func_name = type(node).__name__.upper()
            col = node.find(exp.Column)
            col_name = col.name.upper() if col else "*"
            key = (func_name, col_name)
            if key in seen:
                continue
            # 别名（AS）
            alias = ""
            parent = node.parent
            if isinstance(parent, exp.Alias):
                alias = parent.alias or ""
            aggs.append({"func": func_name, "column": col_name, "alias": alias})
            seen.add(key)
        return aggs


def parse_sql(sql: str, dialect: str = "oracle") -> ParsedSQL:
    """便捷函数：解析 SQL。"""
    return SqlParser().parse(sql, dialect=dialect)

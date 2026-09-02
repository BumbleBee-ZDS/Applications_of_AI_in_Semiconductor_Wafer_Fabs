"""NL2SQL 服务（自然语言转 SQL）。

编排流程：
1. :class:`SemanticSearchService` 检索相关表/字段
2. :class:`JoinPathFinder` 计算多表 JOIN 路径
3. 组装 Schema 上下文（DDL + JOIN 条件 + 示例）
4. :class:`LLMClient` 生成 SQL
5. 可选：:class:`SqlParser` 校验生成 SQL 的合法性

对应ResNet端到端推理：检索增强 + 图谱约束 + LLM 生成。
"""
from __future__ import annotations

import logging
from typing import Any

from fabgraph.config import Settings, get_settings
from fabgraph.graph.graph_algorithms import JoinPathFinder
from fabgraph.graph.graph_utils import to_join_graph
from fabgraph.models.semantic import NL2SQLRequest, NL2SQLResponse, SearchResult
from fabgraph.repository.metadata_repo import MetadataRepository
from fabgraph.service.semantic_service import SemanticSearchService
from fabgraph.utils.exceptions import NL2SQLError
from fabgraph.utils.llm_client import LLMClient
from fabgraph.utils.sql_parser import SqlParser

logger = logging.getLogger(__name__)


class NL2SQLService:
    """自然语言转 SQL 服务。

    依赖 :class:`SemanticSearchService`、:class:`LLMClient`，
    可通过构造函数注入便于测试。
    """

    def __init__(
        self,
        semantic_service: SemanticSearchService | None = None,
        llm_client: LLMClient | None = None,
        metadata_repo: MetadataRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        """初始化 NL2SQL 服务。

        Args:
            semantic_service: 语义检索服务。
            llm_client: LLM 客户端。
            metadata_repo: 元数据仓储。
            settings: 配置对象。
        """
        self._settings = settings or get_settings()
        self.metadata_repo = metadata_repo or MetadataRepository(self._settings)
        self.semantic_service = semantic_service or SemanticSearchService(
            metadata_repo=self.metadata_repo, settings=self._settings,
        )
        self.llm_client = llm_client or LLMClient(self._settings)
        self._parser = SqlParser()

    def generate(self, request: NL2SQLRequest) -> NL2SQLResponse:
        """生成 SQL。

        Args:
            request: NL2SQL 请求（含自然语言问题）。

        Returns:
            :class:`NL2SQLResponse` 含生成 SQL、相关表、JOIN 路径。
        """
        # 1. 语义检索相关表
        results = self.semantic_service.search_tables(
            request.question, top_k=request.top_k, expand=True
        )
        if not results:
            raise NL2SQLError("语义检索未返回任何相关表")

        table_names = [r.table_name for r in results if r.table_name]
        # 2. 计算 JOIN 路径（若多表）
        join_paths = self._compute_join_paths(table_names)

        # 3. 组装上下文
        context = self._build_context(results, join_paths)

        # 4. 调用 LLM 生成 SQL
        prompt = self._build_prompt(request.question, context)
        sql = self.llm_client.chat(prompt, system=self._system_prompt())

        # 5. 后处理
        sql = self._postprocess_sql(sql)
        confidence = self._estimate_confidence(results, sql)

        return NL2SQLResponse(
            question=request.question,
            sql=sql,
            related_tables=table_names,
            join_paths=join_paths,
            context=context,
            confidence=confidence,
            is_validated=self._validate_sql(sql),
            mock_mode=self.llm_client.use_mock,
        )

    def _compute_join_paths(
        self, table_names: list[str]
    ) -> list[dict[str, Any]]:
        """计算多表 JOIN 路径。

        Args:
            table_names: 相关表名列表。

        Returns:
            JOIN 路径字典列表 [{start, end, path, conditions}]。
        """
        if len(table_names) < 2:
            return []
        # 从 Schema Graph 构建 JOIN 图
        graph = self._get_join_graph()
        if graph is None or graph.number_of_edges() == 0:
            return []
        finder = JoinPathFinder(graph)
        try:
            paths = finder.find_multi_table_path(table_names, max_hops=3)
        except NL2SQLError as e:
            logger.warning("JOIN 路径计算失败: %s", e)
            return []
        return [
            {
                "start": p.start_table, "end": p.end_table,
                "path": p.path, "conditions": p.join_conditions,
                "weight": p.total_weight,
            }
            for p in paths
        ]

    def _get_join_graph(self):
        """获取 JOIN 图（从语义服务缓存的 Schema Graph 投影）。"""
        sg = self.semantic_service._schema_graph
        if sg is None:
            return None
        return to_join_graph(sg)

    def _build_context(
        self, results: list[SearchResult], join_paths: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """组装 LLM 上下文。"""
        tables_ctx: list[dict[str, Any]] = []
        for r in results:
            table_name = r.table_name
            if not table_name:
                continue
            table = self.metadata_repo.get_table_by_name(table_name)
            if not table:
                continue
            tables_ctx.append({
                "name": table.table_name,
                "description": table.description,
                "columns": [
                    {
                        "name": c.column_name, "type": c.data_type,
                        "desc": c.description, "semantic": c.semantic_type.value,
                    }
                    for c in table.columns
                ],
            })
        return {"tables": tables_ctx, "join_paths": join_paths}

    def _build_prompt(self, question: str, context: dict[str, Any]) -> str:
        """组装 LLM prompt。"""
        lines = [f"问题：{question}", "", "相关表结构："]
        for t in context.get("tables", []):
            lines.append(f"- {t['name']}: {t['description']}")
            for c in t["columns"]:
                lines.append(
                    f"  - {c['name']} ({c['type']}): {c['desc']} [{c['semantic']}]"
                )
        joins = context.get("join_paths", [])
        if joins:
            lines.extend(["", "建议 JOIN 路径："])
            for jp in joins:
                lines.append(f"  {jp['start']} -> {jp['end']}: {' AND '.join(jp['conditions'])}")
        lines.extend(["", "请生成 Oracle 方言 SQL："])
        return "\n".join(lines)

    @staticmethod
    def _system_prompt() -> str:
        """LLM 系统 prompt。"""
        return (
            "你是 FabGraph 的 NL2SQL 助手。根据给定的表结构和 JOIN 路径，"
            "生成 Oracle 方言的 SELECT 语句。仅输出 SQL，不要解释。"
        )

    @staticmethod
    def _postprocess_sql(sql: str) -> str:
        """后处理 LLM 输出：去除 markdown 包裹与多余空白。"""
        sql = sql.strip()
        # 去除 ```sql ... ``` 包裹
        if sql.startswith("```"):
            lines = sql.split("\n")
            # 去首尾 ``` 行
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sql = "\n".join(lines).strip()
        return sql

    def _validate_sql(self, sql: str) -> bool:
        """校验生成 SQL 是否可解析。"""
        try:
            self._parser.parse(sql)
            return True
        except Exception:
            return False

    @staticmethod
    def _estimate_confidence(
        results: list[SearchResult], sql: str
    ) -> float:
        """估算生成置信度。

        基于检索分数均值与 SQL 是否非空。
        """
        if not sql:
            return 0.0
        avg_score = sum(r.score for r in results) / len(results) if results else 0.0
        # 简单加权
        return min(1.0, avg_score * 0.6 + 0.3)

"""LLM 客户端。

封装 OpenAI / DeepSeek 调用，统一接口 :meth:`LLMClient.chat`。
DeepSeek 兼容 OpenAI SDK，通过 ``base_url`` 切换。

Mock 模式（``use_mock=True`` 或无 API Key 时启用）：
基于 prompt 关键词匹配返回预设响应，保证无网络环境下可运行。
对应ResNet输出头：LLM 作为最终分类头，Mock 为兜底推理。
"""
from __future__ import annotations

import logging
from typing import Any

from fabgraph.config import Settings, get_settings
from fabgraph.utils.exceptions import LLMError

logger = logging.getLogger(__name__)

# openai SDK 可选
try:
    from openai import OpenAI  # type: ignore

    _HAS_OPENAI = True
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore
    _HAS_OPENAI = False


class LLMClient:
    """LLM 客户端（OpenAI / DeepSeek 兼容）。

    Attributes:
        use_mock: 是否走 Mock 模式。
        model: 当前模型名。
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化 LLM 客户端。

        Args:
            settings: 配置对象，默认全局单例。
        """
        self._settings = settings or get_settings()
        self._llm_cfg = self._settings.llm
        self._provider_cfg = self._llm_cfg.active()
        # Mock 条件：显式 use_mock 或无 API Key 或 SDK 缺失
        self.use_mock = (
            self._llm_cfg.use_mock
            or not self._llm_cfg.has_api_key()
            or not _HAS_OPENAI
        )
        self.model = self._provider_cfg.model or "mock-model"
        self._client: Any = None
        if not self.use_mock:
            self._client = OpenAI(
                api_key=self._provider_cfg.api_key,
                base_url=self._provider_cfg.base_url or None,
            )
        logger.info(
            "LLM 客户端初始化: provider=%s mock=%s model=%s",
            self._llm_cfg.provider, self.use_mock, self.model,
        )

    def chat(
        self,
        prompt: str,
        system: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """同步对话接口。

        Args:
            prompt: 用户 prompt。
            system: 系统 prompt（可选）。
            temperature: 采样温度，默认用配置值。
            max_tokens: 最大生成 token 数。

        Returns:
            LLM 生成的文本。

        Raises:
            LLMError: 调用失败。
        """
        if self.use_mock:
            return self._mock_chat(prompt, system)
        return self._real_chat(prompt, system, temperature, max_tokens)

    def _real_chat(
        self,
        prompt: str,
        system: str,
        temperature: float | None,
        max_tokens: int | None,
    ) -> str:
        """真实 LLM 调用。"""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=self.model,
                messages=messages,
                temperature=self._provider_cfg.temperature
                if temperature is None
                else temperature,
                max_tokens=self._provider_cfg.max_tokens
                if max_tokens is None
                else max_tokens,
            )
        except Exception as e:
            raise LLMError(f"LLM 调用失败: {e}") from e
        content = resp.choices[0].message.content or ""
        logger.debug("LLM 响应: %s", content[:200])
        return content

    # ---------------- Mock 模式 ----------------

    def _mock_chat(self, prompt: str, system: str) -> str:
        """Mock 对话：基于 prompt 关键词返回预设响应。

        支持 NL2SQL 与语义推断两类场景。
        """
        prompt_lower = prompt.lower()
        # NL2SQL 场景：prompt 含 "sql" 且包含表名
        if "sql" in prompt_lower or "查询" in prompt or "select" in prompt_lower:
            sql = self._mock_nl2sql(prompt)
            if sql:
                return sql
        # 语义推断场景：prompt 含 "semantic" 或 "字段"
        if "semantic" in prompt_lower or "字段" in prompt or "column" in prompt_lower:
            return self._mock_semantic_inference(prompt)
        # 默认响应
        return "[Mock LLM] 已收到请求，但未匹配预设场景。"

    @staticmethod
    def _mock_nl2sql(prompt: str) -> str:
        """根据 prompt 中提及的表名生成 Mock SQL。"""
        # 识别 prompt 中出现的表名（大写关键词）
        table_keywords = [
            "LOT_HISTORY", "WAFER_RESULT", "EQUIPMENT_LOG", "SPC_DATA",
            "RECIPE_PARAM", "DEFECT_DATA", "PROCESS_FLOW", "YIELD_SUMMARY",
        ]
        found = [t for t in table_keywords if t in prompt.upper()]
        if not found:
            return ""
        # 简单 SELECT 模板
        main_table = found[0]
        cols = "LOT_ID, PRODUCT_ID" if "LOT_HISTORY" in found else "*"
        sql = f"SELECT {cols} FROM {main_table}"
        # 多表则加 JOIN
        if len(found) > 1:
            join_table = found[1]
            sql += f" JOIN {join_table} ON {main_table}.WFR_ID = {join_table}.WFR_ID"
        # 良率类问题加 WHERE
        if "良率" in prompt or "yield" in prompt.lower():
            sql += " WHERE YIELD_VAL < 0.9"
        elif "缺陷" in prompt or "defect" in prompt.lower():
            sql += " WHERE DEFECT_CNT > 10"
        return sql + ";"

    @staticmethod
    def _mock_semantic_inference(prompt: str) -> str:
        """Mock 语义推断响应。"""
        # 简单关键词映射
        if "良率" in prompt or "yield" in prompt.lower():
            return "measure:YIELD_VAL:良率值:0.9"
        if "缺陷" in prompt or "defect" in prompt.lower():
            return "measure:DEFECT_CNT:缺陷数:0.9"
        if "批次" in prompt or "lot" in prompt.lower():
            return "dimension:LOT_ID:批次号:1.0"
        if "设备" in prompt or "equipment" in prompt.lower():
            return "dimension:EQP_ID:设备号:0.9"
        return "unknown::未知字段:0.0"

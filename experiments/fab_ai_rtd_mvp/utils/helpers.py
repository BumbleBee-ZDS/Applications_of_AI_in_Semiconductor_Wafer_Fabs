"""通用工具函数与 Streamlit 会话状态管理。"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from typing import Any


def now_iso() -> str:
    """当前时间字符串（%Y-%m-%d %H:%M:%S）。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_trace_id() -> str:
    """生成全链路追踪 ID，如 TRACE-20260819-143052-4F2A。"""
    return f"TRACE-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4].upper()}"


def parse_json_response(text: str) -> dict[str, Any]:
    """容错解析大模型 JSON 输出。

    - 剥离 ```json ... ``` 围栏；
    - 截取首个 ``{`` 到最后一个 ``}`` 之间的内容；
    - ``json.loads`` 失败时抛出 ``ValueError``。

    Args:
        text: 模型返回的原始文本。

    Returns:
        解析后的 JSON 字典。

    Raises:
        ValueError: 响应为空或未包含合法 JSON 对象。
    """
    if not text or not text.strip():
        raise ValueError("模型返回为空")
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.S)
    if fence:
        cleaned = fence.group(1).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"响应中未找到 JSON 对象：{text[:200]!r}")
    return json.loads(cleaned[start : end + 1])


def init_session_state() -> None:
    """初始化所有页面共享的 session_state 键（幂等，可在任意页面调用）。"""
    import streamlit as st  # 延迟导入，避免模块级依赖 Streamlit

    defaults: dict[str, Any] = {
        "factory_state": None,
        "events": [],
        "diagnoses": [],
        "strategy": None,
        "rl_results": [],
        "last_trace_id": None,
        "execution_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "approval_store" not in st.session_state:
        from agents.execution_agent import ApprovalStore

        st.session_state["approval_store"] = ApprovalStore()
    if "audit_agent" not in st.session_state:
        from agents.audit_agent import AuditAgent

        st.session_state["audit_agent"] = AuditAgent()

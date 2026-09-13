"""LLM 调用统一封装：超时、重试、异常降级到 Mock 并提示。

这是 compiler 与 text2sql 共享的真实 LLM 入口。
- 未配置 Key：一律返回 None（调用方走 Mock）
- 调用异常：告警降级，返回 None
"""
from __future__ import annotations

from typing import Callable, Sequence

import config


def _build_client():
    from openai import OpenAI
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL,
                  timeout=config.LLM_TIMEOUT_SECONDS)


def chat_complete(system: str, user: str,
                  on_error: Callable[[str], None] | None = None) -> str | None:
    """调用 LLM，返回文本；失败/未配置 Key 返回 None 并回调告警。

    - 超时 = config.LLM_TIMEOUT_SECONDS
    - 最多重试 config.LLM_MAX_RETRIES 次
    """
    if not config.LLM_AVAILABLE:
        return None
    client = _build_client()
    last_err = ""
    for attempt in range(config.LLM_MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            text = (resp.choices[0].message.content or "").strip()
            if text:
                return text
            last_err = "空响应"
        except Exception as e:  # noqa: BLE001 - 统一降级
            last_err = str(e)
    if on_error:
        on_error(f"LLM 调用失败（已降级到 Mock）：{last_err}")
    return None
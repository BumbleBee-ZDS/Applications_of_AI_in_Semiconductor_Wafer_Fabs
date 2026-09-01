"""LLM 客户端封装：DeepSeek（聊天 / 推理）+ 阿里千问（文本向量化）。

两者均走 OpenAI SDK 兼容协议：
- DeepSeek:  base_url = https://api.deepseek.com，模型 deepseek-v4-flash / deepseek-v4-pro
- 千问:      base_url = DASHSCOPE_BASE_URL（compatible-mode/v1），模型 qwen3.7-text-embedding

未配置 API Key 时抛出 :class:`LLMNotConfiguredError`，由上层 Agent 做规则降级，
保证应用在无 Key / 网络异常时仍可完整演示。
"""

from __future__ import annotations

import os
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

# 首次导入时加载 .env（幂等，重复调用无副作用）
load_dotenv()

# ---------- 环境变量 ----------
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "").strip()
DASHSCOPE_BASE_URL: str = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
).strip()
try:
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1024"))
except ValueError:
    EMBEDDING_DIM = 1024

# ---------- 端点与模型 ----------
DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
DEEPSEEK_LIGHT_MODEL: str = "deepseek-v4-flash"    # 轻量任务：分类 / 摘要
DEEPSEEK_HEAVY_MODEL: str = "deepseek-v4-pro"      # 强模型：根因分析 / 调度决策
QWEN_EMBEDDING_MODEL: str = "qwen3.7-text-embedding"


class LLMNotConfiguredError(RuntimeError):
    """未配置对应 API Key 时的统一异常。"""


def is_deepseek_ready() -> bool:
    """DeepSeek 是否已配置 API Key。"""
    return bool(DEEPSEEK_API_KEY)


def is_dashscope_ready() -> bool:
    """千问 DashScope 是否已配置 API Key。"""
    return bool(DASHSCOPE_API_KEY)


def chat_deepseek(
    messages: list[dict[str, str]],
    model: str = DEEPSEEK_HEAVY_MODEL,
    temperature: float = 0.3,
    response_format: Optional[dict[str, str]] = None,
    max_tokens: int = 2000,
) -> str:
    """调用 DeepSeek 聊天补全，返回模型输出文本。

    Args:
        messages: OpenAI 格式的对话消息列表。
        model: 模型名，默认 DEEPSEEK_HEAVY_MODEL（deepseek-v4-pro）。
        temperature: 采样温度，根因分析等任务建议 0.2~0.3。
        response_format: 例如 ``{"type": "json_object"}`` 强制模型输出 JSON。
        max_tokens: 最大生成 token 数。

    Returns:
        模型回复的文本内容。

    Raises:
        LLMNotConfiguredError: 未配置 ``DEEPSEEK_API_KEY``。
        Exception: 透传上游 API / 网络错误，由调用方统一兜底降级。
    """
    if not is_deepseek_ready():
        raise LLMNotConfiguredError("未检测到 DEEPSEEK_API_KEY，请先复制 .env.example 为 .env 并填入 Key")

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, timeout=60.0)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format is not None:
        kwargs["response_format"] = response_format

    resp = client.chat.completions.create(**kwargs)
    if not resp.choices:
        raise RuntimeError("DeepSeek 返回空响应")
    return resp.choices[0].message.content or ""


def embed_texts(texts: list[str], text_type: str = "document") -> list[list[float]]:
    """调用阿里千问文本向量化模型生成 embedding。

    Args:
        texts: 待向量化文本列表（一次一批）。
        text_type: ``"query"``（查询文本）或 ``"document"``（知识文档），
                   通过 ``extra_body`` 透传给千问接口。

    Returns:
        embedding 列表，每个为 ``float`` 列表，维度见 :data:`EMBEDDING_DIM`。

    Raises:
        LLMNotConfiguredError: 未配置 ``DASHSCOPE_API_KEY``。
        Exception: 透传上游 API / 网络错误。
    """
    if not is_dashscope_ready():
        raise LLMNotConfiguredError("未检测到 DASHSCOPE_API_KEY，请先复制 .env.example 为 .env 并填入 Key")

    client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL, timeout=60.0)
    resp = client.embeddings.create(
        model=QWEN_EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIM,
        encoding_format="float",
        extra_body={"text_type": text_type},  # 区分 query / document
    )
    ordered = sorted(resp.data, key=lambda item: item.index)
    return [item.embedding for item in ordered]

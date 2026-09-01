"""LLM 客户端测试。"""
from __future__ import annotations

import pytest

from fabgraph.utils.exceptions import LLMError
from fabgraph.utils.llm_client import LLMClient


def test_mock_mode_default(tmp_settings):
    """默认配置应启用 Mock 模式（use_mock=True）。"""
    client = LLMClient(tmp_settings)
    assert client.use_mock is True


def test_mock_chat_nl2sql(tmp_settings):
    """Mock 模式 NL2SQL 场景应返回 SELECT 语句。"""
    client = LLMClient(tmp_settings)
    resp = client.chat("请生成查询 LOT_HISTORY 良率的 SQL")
    assert "SELECT" in resp.upper()
    assert "LOT_HISTORY" in resp


def test_mock_chat_join(tmp_settings):
    """Mock 模式多表 JOIN 场景。"""
    client = LLMClient(tmp_settings)
    resp = client.chat("生成 SQL 查询 LOT_HISTORY JOIN WAFER_RESULT")
    assert "JOIN" in resp.upper()
    assert "LOT_HISTORY" in resp
    assert "WAFER_RESULT" in resp


def test_mock_chat_semantic(tmp_settings):
    """Mock 模式语义推断场景。"""
    client = LLMClient(tmp_settings)
    resp = client.chat("请推断这个字段的 semantic type: 良率 yield")
    assert "measure" in resp.lower() or "YIELD" in resp


def test_mock_chat_default(tmp_settings):
    """Mock 模式无匹配场景返回默认响应。"""
    client = LLMClient(tmp_settings)
    resp = client.chat("hello world")
    assert "Mock" in resp or len(resp) > 0


def test_chat_with_system_prompt(tmp_settings):
    """带 system prompt 的对话应正常返回。"""
    client = LLMClient(tmp_settings)
    resp = client.chat("查询 SQL LOT_HISTORY", system="你是助手")
    assert isinstance(resp, str)
    assert len(resp) > 0


def test_mock_yield_filter(tmp_settings):
    """Mock NL2SQL 良率问题应加 WHERE 条件。"""
    client = LLMClient(tmp_settings)
    resp = client.chat("查询 LOT_HISTORY 的 SQL，关注良率 yield")
    assert "WHERE" in resp.upper()

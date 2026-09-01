"""嵌入客户端测试。"""
from __future__ import annotations

import pytest

from fabgraph.utils.embeddings import EmbeddingClient


def test_mock_mode_default(tmp_settings):
    """默认配置应启用 Mock 模式。"""
    client = EmbeddingClient(tmp_settings)
    assert client.use_mock is True


def test_embed_returns_correct_dimension(tmp_settings):
    """嵌入维度应等于配置 dimension。"""
    client = EmbeddingClient(tmp_settings)
    vecs = client.embed(["hello world", "foo bar"])
    assert len(vecs) == 2
    for v in vecs:
        assert len(v) == client.dimension


def test_embed_one(tmp_settings):
    """embed_one 返回单条向量。"""
    client = EmbeddingClient(tmp_settings)
    vec = client.embed_one("test text")
    assert len(vec) == client.dimension


def test_embed_empty(tmp_settings):
    """空列表应返回空。"""
    client = EmbeddingClient(tmp_settings)
    assert client.embed([]) == []


def test_embed_deterministic(tmp_settings):
    """相同文本应产生相同向量（Mock 确定性）。"""
    client = EmbeddingClient(tmp_settings)
    v1 = client.embed_one("lot history yield")
    v2 = client.embed_one("lot history yield")
    assert v1 == v2


def test_embed_different_texts_differ(tmp_settings):
    """不同文本应产生不同向量。"""
    client = EmbeddingClient(tmp_settings)
    v1 = client.embed_one("lot history yield")
    v2 = client.embed_one("equipment defect count")
    assert v1 != v2


def test_embed_batch(tmp_settings):
    """批量嵌入。"""
    client = EmbeddingClient(tmp_settings)
    texts = [f"text sample {i}" for i in range(10)]
    vecs = client.embed(texts)
    assert len(vecs) == 10
    assert all(len(v) == client.dimension for v in vecs)

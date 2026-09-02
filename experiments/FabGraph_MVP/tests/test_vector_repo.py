"""VectorRepository 测试（numpy 兜底模式）。"""
from __future__ import annotations

import pytest

from fabgraph.models.semantic import EmbeddingItem
from fabgraph.utils.exceptions import EmbeddingError, SearchError


def _make_item(item_id: str, vector: list[float], text: str = "") -> EmbeddingItem:
    return EmbeddingItem(item_id=item_id, text=text, vector=vector)


def _vec(repo, *values: float) -> list[float]:
    """构造 repo.dimension 维向量，前 len(values) 位填充 values，其余补 0。"""
    v = [0.0] * repo.dimension
    for i, val in enumerate(values):
        v[i] = val
    return v


def test_upsert_and_search(vector_repo):
    """upsert 后能检索到相似项。"""
    items = [
        _make_item("t1", _vec(vector_repo, 1.0)),
        _make_item("t2", _vec(vector_repo, 0.0, 1.0)),
        _make_item("t3", _vec(vector_repo, 1.0, 1.0)),
    ]
    n = vector_repo.upsert(items)
    assert n == 3
    assert len(vector_repo) == 3

    # 查询与 t1 最相似的
    results = vector_repo.search(_vec(vector_repo, 1.0), top_k=2)
    assert len(results) == 2
    # t1 自身应排第一（内积=1）
    assert results[0][0].item_id == "t1"


def test_upsert_dimension_mismatch(vector_repo):
    """维度不匹配应抛 EmbeddingError。"""
    with pytest.raises(EmbeddingError):
        vector_repo.upsert([_make_item("x", [1.0, 2.0])])  # 维度=2


def test_search_empty_repo(vector_repo):
    """空仓储检索应抛 SearchError。"""
    with pytest.raises(SearchError):
        vector_repo.search([0.0] * vector_repo.dimension)


def test_search_query_dimension_mismatch(vector_repo):
    """查询维度不匹配应抛 SearchError。"""
    vector_repo.upsert([_make_item("t1", [1.0] * vector_repo.dimension)])
    with pytest.raises(SearchError):
        vector_repo.search([1.0, 0.0])


def test_upsert_replaces_existing(vector_repo):
    """相同 item_id 应覆盖旧项。"""
    vector_repo.upsert([_make_item("t1", [1.0] * vector_repo.dimension)])
    vector_repo.upsert([_make_item("t1", [0.0] * vector_repo.dimension)])
    assert len(vector_repo) == 1
    results = vector_repo.search([1.0] * vector_repo.dimension, top_k=1)
    # t1 现在是全零向量，内积应为 0
    assert results[0][0].item_id == "t1"
    assert results[0][1] == 0.0


def test_save_and_load(vector_repo):
    """持久化与加载一致。"""
    items = [
        _make_item("t1", _vec(vector_repo, 1.0), "table1"),
        _make_item("t2", _vec(vector_repo, 0.0, 1.0), "table2"),
    ]
    vector_repo.upsert(items)
    path = vector_repo.save()
    assert path.exists()

    # 新仓储加载
    from fabgraph.repository.vector_repo import VectorRepository
    new_repo = VectorRepository(vector_repo._settings)
    n = new_repo.load()
    assert n == 2
    assert len(new_repo) == 2
    # 加载后能检索
    results = new_repo.search(_vec(vector_repo, 1.0), top_k=1)
    assert results[0][0].item_id == "t1"


def test_load_nonexistent(vector_repo):
    """加载不存在的文件返回 0。"""
    n = vector_repo.load()
    assert n == 0

"""向量索引仓储（FAISS 骨架）。

本步搭建骨架：
- 持有 :class:`EmbeddingItem` 列表与 numpy 矩阵
- 提供 upsert / search / save / load 接口
- FAISS 未安装时降级为 numpy 暴力检索，保证 MVP 可运行

后续 Step 3 接入真实嵌入模型时只需替换 :meth:`_ensure_index`。
对应ResNet嵌入头：将语义特征投影到向量空间供近邻检索。
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from fabgraph.config import Settings, get_settings, project_root
from fabgraph.models.semantic import EmbeddingItem
from fabgraph.utils.exceptions import EmbeddingError, SearchError

logger = logging.getLogger(__name__)

# FAISS 可选，缺失时降级
try:
    import faiss  # type: ignore

    _HAS_FAISS = True
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore
    _HAS_FAISS = False
    logger.warning("未安装 faiss-cpu，向量检索降级为 numpy 暴力实现")


class VectorRepository:
    """向量索引仓储。

    Attributes:
        dimension: 向量维度。
        index_path: 索引持久化路径。
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化向量仓储。

        Args:
            settings: 配置对象，默认使用全局单例。
        """
        self._settings = settings or get_settings()
        self.dimension = self._settings.embedding.dimension
        self.index_path = self._resolve_path(
            self._settings.vector.faiss_index_path
        )
        self._items: list[EmbeddingItem] = []
        self._matrix: np.ndarray | None = None
        self._index: Any = None  # faiss.Index | None
        self._built = False

    def _resolve_path(self, path: str | Path) -> Path:
        """相对路径解析为基于项目根的绝对路径。"""
        p = Path(path)
        if not p.is_absolute():
            p = project_root() / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # ---------------- 写入 ----------------

    def upsert(self, items: list[EmbeddingItem]) -> int:
        """批量插入或覆盖向量项。

        相同 item_id 的旧项被替换。

        Args:
            items: 待写入的向量项列表。

        Returns:
            实际写入条数。

        Raises:
            EmbeddingError: 向量维度不匹配。
        """
        if not items:
            return 0
        existing = {it.item_id: i for i, it in enumerate(self._items)}
        for it in items:
            if len(it.vector) != self.dimension:
                raise EmbeddingError(
                    f"向量维度不匹配: 期望 {self.dimension} 实际 {len(it.vector)}"
                )
            if it.item_id in existing:
                self._items[existing[it.item_id]] = it
            else:
                existing[it.item_id] = len(self._items)
                self._items.append(it)
        self._built = False
        logger.info("向量仓储 upsert: %d 项 (总计 %d)", len(items), len(self._items))
        return len(items)

    def build_index(self) -> None:
        """构建底层索引（FAISS 或 numpy 兜底）。"""
        if not self._items:
            self._matrix = np.zeros((0, self.dimension), dtype=np.float32)
            self._index = None
            self._built = True
            return
        self._matrix = np.array(
            [it.vector for it in self._items], dtype=np.float32
        )
        if _HAS_FAISS:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._index.add(self._matrix)  # type: ignore[union-attr]
        else:
            self._index = None
        self._built = True
        logger.info("向量索引构建完成: %d 项 (FAISS=%s)",
                    len(self._items), _HAS_FAISS)

    def _ensure_index(self) -> None:
        """确保索引已构建。"""
        if not self._built:
            self.build_index()

    # ---------------- 检索 ----------------

    def search(
        self, query: list[float], top_k: int = 10
    ) -> list[tuple[EmbeddingItem, float]]:
        """最近邻检索。

        Args:
            query: 查询向量。
            top_k: 返回前 K 条。

        Returns:
            (item, score) 元组列表，按相似度降序。

        Raises:
            SearchError: 仓储为空或维度不匹配。
        """
        self._ensure_index()
        if not self._items:
            raise SearchError("向量仓储为空，无法检索")
        if len(query) != self.dimension:
            raise SearchError(
                f"查询向量维度不匹配: 期望 {self.dimension} 实际 {len(query)}"
            )
        q = np.array(query, dtype=np.float32).reshape(1, -1)
        if _HAS_FAISS and self._index is not None:
            scores, indices = self._index.search(q, top_k)  # type: ignore[union-attr]
            pairs = [
                (self._items[i], float(s))
                for s, i in zip(scores[0], indices[0])
                if i >= 0
            ]
        else:
            pairs = self._brute_force_search(q, top_k)
        return pairs

    def _brute_force_search(
        self, q: np.ndarray, top_k: int
    ) -> list[tuple[EmbeddingItem, float]]:
        """numpy 暴力检索（FAISS 缺失时兜底）。"""
        assert self._matrix is not None
        # 内积相似度
        scores = self._matrix @ q.T
        scores = scores.flatten()
        k = min(top_k, len(scores))
        top_idx = np.argsort(-scores)[:k]
        return [(self._items[i], float(scores[i])) for i in top_idx]

    # ---------------- 持久化 ----------------

    def save(self) -> Path:
        """持久化向量仓储（pickle 快照）。

        Returns:
            写入文件路径。

        Raises:
            EmbeddingError: 写入失败。
        """
        try:
            with open(self.index_path, "wb") as f:
                pickle.dump(
                    {"dimension": self.dimension, "items": self._items},
                    f,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
        except OSError as e:
            raise EmbeddingError(f"向量仓储持久化失败: {e}") from e
        logger.info("向量仓储已持久化: %s (项数=%d)", self.index_path, len(self._items))
        return self.index_path

    def load(self) -> int:
        """加载向量仓储。

        Returns:
            加载的项数。

        Raises:
            EmbeddingError: 文件不存在或加载失败。
        """
        if not self.index_path.exists():
            logger.warning("向量仓储文件不存在: %s", self.index_path)
            return 0
        try:
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
        except (OSError, pickle.UnpicklingError) as e:
            raise EmbeddingError(f"向量仓储加载失败: {e}") from e
        self._items = data.get("items", [])
        self.dimension = data.get("dimension", self.dimension)
        self._built = False
        logger.info("向量仓储已加载: %d 项", len(self._items))
        return len(self._items)

    def __len__(self) -> int:
        """返回当前项数。"""
        return len(self._items)

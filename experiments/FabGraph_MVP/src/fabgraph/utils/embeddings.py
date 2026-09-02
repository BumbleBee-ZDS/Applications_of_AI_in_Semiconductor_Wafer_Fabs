"""向量嵌入客户端。

封装 sentence-transformers 模型调用，统一接口 :meth:`EmbeddingClient.embed`。

Mock 模式（``use_mock=True`` 或模型未安装时启用）：
基于 TF-IDF（sklearn）+ 哈希降维生成确定性向量，
保证无 GPU / 无模型下载环境下可运行。
对应ResNet嵌入层：将文本特征投影到固定维度的向量空间。
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import numpy as np

from fabgraph.config import Settings, get_settings
from fabgraph.utils.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# sentence-transformers 可选
try:
    from sentence_transformers import SentenceTransformer  # type: ignore

    _HAS_ST = True
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore
    _HAS_ST = False

# sklearn 用于 Mock TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore

    _HAS_SKLEARN = True
except ImportError:  # pragma: no cover
    TfidfVectorizer = None  # type: ignore
    _HAS_SKLEARN = False


class EmbeddingClient:
    """向量嵌入客户端。

    Attributes:
        use_mock: 是否走 Mock 模式。
        dimension: 输出向量维度。
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化嵌入客户端。

        Args:
            settings: 配置对象，默认全局单例。
        """
        self._settings = settings or get_settings()
        self._cfg = self._settings.embedding
        self.dimension = self._cfg.dimension
        self.use_mock = self._cfg.use_mock or not _HAS_ST
        self._model: Any = None
        self._tfidf: Any = None
        self._fitted = False
        if not self.use_mock:
            try:
                self._model = SentenceTransformer(self._cfg.model_name)
                # 用模型实际维度覆盖配置
                self.dimension = self._model.get_sentence_embedding_dimension()
                logger.info("嵌入模型加载: %s dim=%d", self._cfg.model_name, self.dimension)
            except Exception as e:
                logger.warning("模型加载失败，降级 Mock: %s", e)
                self.use_mock = True
                self._model = None
        if self.use_mock and _HAS_SKLEARN:
            self._tfidf = TfidfVectorizer(
                max_features=self.dimension,
                token_pattern=r"(?u)\b\w+\b",
            )
        logger.info("嵌入客户端初始化: mock=%s dim=%d", self.use_mock, self.dimension)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文本。

        Args:
            texts: 待嵌入文本列表。

        Returns:
            与 texts 等长的向量列表，每条维度 = :attr:`dimension`。

        Raises:
            EmbeddingError: 嵌入失败。
        """
        if not texts:
            return []
        if self.use_mock:
            return self._mock_embed(texts)
        return self._real_embed(texts)

    def embed_one(self, text: str) -> list[float]:
        """嵌入单条文本。"""
        return self.embed([text])[0]

    def _real_embed(self, texts: list[str]) -> list[list[float]]:
        """真实模型嵌入。"""
        try:
            vecs = self._model.encode(  # type: ignore[union-attr]
                texts, batch_size=self._cfg.batch_size, show_progress_bar=False,
            )
            return vecs.tolist()
        except Exception as e:
            raise EmbeddingError(f"嵌入失败: {e}") from e

    # ---------------- Mock 模式 ----------------

    def _mock_embed(self, texts: list[str]) -> list[list[float]]:
        """Mock 嵌入：TF-IDF + 哈希降维到固定维度。

        若 sklearn 可用则用 TF-IDF（需先 fit），否则用纯哈希。
        保证相同文本产生相同向量（确定性）。
        """
        if _HAS_SKLEARN and self._tfidf is not None:
            return self._tfidf_embed(texts)
        return self._hash_embed(texts)

    def _tfidf_embed(self, texts: list[str]) -> list[list[float]]:
        """TF-IDF 嵌入（sklearn）。

        首次调用时 fit，后续 transform。维度通过截断/补零对齐。
        """
        assert self._tfidf is not None
        try:
            if not self._fitted:
                self._tfidf.fit(texts)
                self._fitted = True
            mat = self._tfidf.transform(texts).toarray()
        except Exception as e:
            raise EmbeddingError(f"TF-IDF 嵌入失败: {e}") from e
        # 对齐维度
        return self._align_dimension(mat)

    def _hash_embed(self, texts: list[str]) -> list[list[float]]:
        """纯哈希嵌入（无 sklearn 时的兜底）。"""
        mat = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for i, text in enumerate(texts):
            for token in text.lower().split():
                h = hashlib.md5(token.encode("utf-8")).digest()
                idx = int.from_bytes(h[:4], "big") % self.dimension
                mat[i, idx] += 1.0
        # L2 归一化
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        mat = mat / norms
        return mat.tolist()

    def _align_dimension(self, mat: np.ndarray) -> list[list[float]]:
        """将矩阵列数对齐到 self.dimension（截断或补零）。"""
        n, d = mat.shape
        if d == self.dimension:
            return mat.tolist()
        if d > self.dimension:
            return mat[:, : self.dimension].tolist()
        # 补零
        padded = np.zeros((n, self.dimension), dtype=mat.dtype)
        padded[:, :d] = mat
        return padded.tolist()

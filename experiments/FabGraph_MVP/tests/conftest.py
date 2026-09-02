"""pytest 全局夹具与路径配置。

确保 src 目录可被导入，并提供基础 fixtures：
- 临时 Settings（指向 tmp_path）
- 临时 MetadataRepository / GraphRepository / VectorRepository
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 将 src 加入 sys.path，便于直接 import fabgraph
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fabgraph.config import reset_settings_cache, Settings  # noqa: E402
from fabgraph.config import (  # noqa: E402
    AppConfig,
    DatabaseConfig,
    GraphConfig,
    DataConfig,
    VectorConfig,
    EmbeddingConfig,
)
from fabgraph.repository.graph_repo import GraphRepository  # noqa: E402
from fabgraph.repository.metadata_repo import MetadataRepository  # noqa: E402
from fabgraph.repository.vector_repo import VectorRepository  # noqa: E402


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    """返回基于 tmp_path 的 Settings，避免污染仓库目录。"""
    reset_settings_cache()
    settings = Settings(
        app=AppConfig(),
        database=DatabaseConfig(sqlite_path=str(tmp_path / "fabgraph.db")),
        graph=GraphConfig(
            schema_graph_pickle=str(tmp_path / "schema_graph.pkl"),
            lineage_graph_pickle=str(tmp_path / "lineage_graph.pkl"),
        ),
        data=DataConfig(mock_oracle_dir="data/mock_oracle"),
        vector=VectorConfig(faiss_index_path=str(tmp_path / "faiss_index")),
        embedding=EmbeddingConfig(use_mock=True, dimension=64),
    )
    yield settings
    reset_settings_cache()


@pytest.fixture
def metadata_repo(tmp_settings: Settings) -> MetadataRepository:
    """已 init 的 MetadataRepository（空库）。"""
    repo = MetadataRepository(tmp_settings)
    repo.init_db()
    yield repo


@pytest.fixture
def loaded_metadata_repo(metadata_repo: MetadataRepository) -> MetadataRepository:
    """加载了 mock_oracle 数据的 MetadataRepository。"""
    metadata_repo.load_from_json()
    return metadata_repo


@pytest.fixture
def graph_repo(tmp_settings: Settings) -> GraphRepository:
    """GraphRepository（基于 tmp_path）。"""
    return GraphRepository(tmp_settings)


@pytest.fixture
def vector_repo(tmp_settings: Settings) -> VectorRepository:
    """VectorRepository（基于 tmp_path，维度=8）。"""
    return VectorRepository(tmp_settings)

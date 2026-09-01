"""配置加载模块。

加载顺序：
1. ``.env`` 通过 python-dotenv 注入 ``os.environ``。
2. ``configs/settings.yaml`` 读取 YAML，其中 ``${VAR:default}``
   占位符由 ``os.environ`` 展开（环境变量优先于默认值）。
3. 展开后的字典经 Pydantic 校验为 :class:`Settings`。

提供全局单例 :func:`get_settings`，各模块通过依赖注入使用。
对应ResNet配置：超参数集中管理，避免散落各层。
"""
from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from fabgraph.utils.exceptions import ConfigError

logger = logging.getLogger(__name__)

# ${VAR} 或 ${VAR:default} 形式的环境变量占位符
_ENV_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::([^}]*))?\}")


class LLMProviderConfig(BaseModel):
    """单个 LLM Provider 配置。"""

    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.0
    max_tokens: int = 2048


class LLMConfig(BaseModel):
    """LLM 总配置：provider 选择与 Mock 开关。"""

    provider: str = "deepseek"  # openai | deepseek
    use_mock: bool = True
    openai: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    deepseek: LLMProviderConfig = Field(default_factory=LLMProviderConfig)

    def active(self) -> LLMProviderConfig:
        """返回当前 provider 的配置。"""
        return self.openai if self.provider == "openai" else self.deepseek

    def has_api_key(self) -> bool:
        """判断当前 provider 是否配置了 API Key。"""
        return bool(self.active().api_key)


class EmbeddingConfig(BaseModel):
    """向量嵌入配置。"""

    use_mock: bool = True
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32


class DatabaseConfig(BaseModel):
    """数据库配置。"""

    sqlite_path: str = "data/fabgraph.db"


class VectorConfig(BaseModel):
    """向量索引配置。"""

    faiss_index_path: str = "data/faiss_index"
    top_k: int = 10


class GraphConfig(BaseModel):
    """图谱持久化配置。"""

    schema_graph_pickle: str = "data/schema_graph.pkl"
    lineage_graph_pickle: str = "data/lineage_graph.pkl"


class DataConfig(BaseModel):
    """数据目录配置。"""

    mock_oracle_dir: str = "data/mock_oracle"


class SearchConfig(BaseModel):
    """语义搜索配置。"""

    top_k: int = 10
    hop_expansion: int = 1


class NL2SQLConfig(BaseModel):
    """NL2SQL 配置。"""

    max_join_hops: int = 3
    include_lineage: bool = True


class AppConfig(BaseModel):
    """应用顶层配置。"""

    name: str = "FabGraph MVP"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"


class Settings(BaseModel):
    """全局配置聚合。"""

    app: AppConfig = Field(default_factory=AppConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    vector: VectorConfig = Field(default_factory=VectorConfig)
    graph: GraphConfig = Field(default_factory=GraphConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    nl2sql: NL2SQLConfig = Field(default_factory=NL2SQLConfig)


def project_root() -> Path:
    """返回项目根目录。

    Returns:
        项目根目录 Path。
    """
    # src/fabgraph/config.py -> 上溯两级得到项目根
    return Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """加载 .env 文件到 os.environ（不覆盖已存在的环境变量）。"""
    env_path = project_root() / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:  # pragma: no cover
        # 极简兜底：手动解析 KEY=VALUE
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _expand_env_vars(node: Any) -> Any:
    """递归展开 ${VAR:default} 占位符。

    Args:
        node: 配置树的当前节点。

    Returns:
        展开后的配置树（bool/int 自动推断）。
    """
    if isinstance(node, dict):
        return {k: _expand_env_vars(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_expand_env_vars(v) for v in node]
    if isinstance(node, str):
        return _coerce(_ENV_PATTERN.sub(_replace_env, node))
    return node


def _replace_env(match: re.Match[str]) -> str:
    """正则替换回调：用环境变量值替换占位符。"""
    name, default = match.group(1), match.group(2) or ""
    return os.getenv(name, default)


def _coerce(value: str) -> Any:
    """将字符串推断为 bool/int，否则保持字符串。"""
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    if value.lstrip("-").isdigit():
        return int(value)
    return value


def _read_yaml(yaml_path: Path) -> dict[str, Any]:
    """读取并展开 YAML 配置。

    Args:
        yaml_path: settings.yaml 路径。

    Returns:
        展开环境变量后的配置字典。

    Raises:
        ConfigError: YAML 读取或解析失败。
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        raise ConfigError(f"配置文件不存在: {yaml_path}") from e
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML 解析失败: {yaml_path}: {e}") from e
    return _expand_env_vars(raw)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局配置单例。

    Returns:
        :class:`Settings` 实例。

    Raises:
        ConfigError: 配置校验失败。
    """
    _load_dotenv()
    yaml_path = project_root() / "configs" / "settings.yaml"
    if yaml_path.exists():
        data = _read_yaml(yaml_path)
    else:
        logger.warning("未找到 %s，使用默认配置", yaml_path)
        data = {}
    try:
        return Settings(**data)
    except Exception as e:
        raise ConfigError(f"配置校验失败: {e}", details={"raw": str(data)}) from e


def reset_settings_cache() -> None:
    """清除配置单例缓存（测试用）。"""
    get_settings.cache_clear()

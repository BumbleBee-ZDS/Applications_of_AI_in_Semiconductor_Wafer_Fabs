"""图谱持久化仓储。

NetworkX 图谱以 pickle 快照落盘：
- Schema Graph：表/字段/过程节点 + has_column/fk/join_inferred 边
- Lineage Graph：过程作为超边 + reads/writes/lineage 边

pickle 选择：NetworkX 官方推荐的快照方式，加载快、保留全部属性。
对应ResNet模型权重持久化：训练好的"知识"序列化为可复用快照。
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

import networkx as nx

from fabgraph.config import Settings, get_settings, project_root
from fabgraph.utils.exceptions import GraphError

logger = logging.getLogger(__name__)


class GraphRepository:
    """图谱持久化仓储。

    Attributes:
        schema_graph_path: Schema Graph pickle 路径。
        lineage_graph_path: Lineage Graph pickle 路径。
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化图谱仓储。

        Args:
            settings: 配置对象，默认使用全局单例。
        """
        self._settings = settings or get_settings()
        self.schema_graph_path = self._resolve_path(
            self._settings.graph.schema_graph_pickle
        )
        self.lineage_graph_path = self._resolve_path(
            self._settings.graph.lineage_graph_pickle
        )

    def _resolve_path(self, path: str | Path) -> Path:
        """将相对路径解析为基于项目根的绝对路径。"""
        p = Path(path)
        if not p.is_absolute():
            p = project_root() / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # ---------------- Schema Graph ----------------

    def save_schema_graph(self, graph: nx.Graph) -> Path:
        """持久化 Schema Graph。

        Args:
            graph: NetworkX 图对象。

        Returns:
            写入文件路径。

        Raises:
            GraphError: 序列化失败。
        """
        return self._write_pickle(self.schema_graph_path, graph, "Schema Graph")

    def load_schema_graph(self) -> nx.Graph | None:
        """加载 Schema Graph。

        Returns:
            NetworkX 图对象；文件不存在返回 None。
        """
        return self._read_pickle(self.schema_graph_path, "Schema Graph")

    # ---------------- Lineage Graph ----------------

    def save_lineage_graph(self, graph: nx.Graph) -> Path:
        """持久化 Lineage Graph。

        Args:
            graph: NetworkX 图对象（含超边属性）。

        Returns:
            写入文件路径。
        """
        return self._write_pickle(self.lineage_graph_path, graph, "Lineage Graph")

    def load_lineage_graph(self) -> nx.Graph | None:
        """加载 Lineage Graph。

        Returns:
            NetworkX 图对象；文件不存在返回 None。
        """
        return self._read_pickle(self.lineage_graph_path, "Lineage Graph")

    # ---------------- 通用读写 ----------------

    def _write_pickle(
        self, path: Path, obj: Any, label: str
    ) -> Path:
        """写入 pickle 文件。

        Args:
            path: 目标文件路径。
            obj: 可序列化对象。
            label: 日志标签。

        Returns:
            写入文件路径。

        Raises:
            GraphError: 写入失败。
        """
        try:
            with open(path, "wb") as f:
                pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        except (OSError, pickle.PicklingError) as e:
            raise GraphError(f"{label} 持久化失败: {e}") from e
        logger.info("%s 已持久化: %s (节点=%s 边=%s)",
                    label, path,
                    getattr(obj, "number_of_nodes", lambda: "?")(),
                    getattr(obj, "number_of_edges", lambda: "?")())
        return path

    def _read_pickle(self, path: Path, label: str) -> Any:
        """读取 pickle 文件。

        Args:
            path: 源文件路径。
            label: 日志标签。

        Returns:
            反序列化对象；文件不存在返回 None。

        Raises:
            GraphError: 反序列化失败。
        """
        if not path.exists():
            logger.warning("%s pickle 不存在: %s", label, path)
            return None
        try:
            with open(path, "rb") as f:
                obj = pickle.load(f)
        except (OSError, pickle.UnpicklingError) as e:
            raise GraphError(f"{label} 加载失败: {e}") from e
        logger.info("%s 已加载: %s (节点=%s 边=%s)",
                    label, path,
                    getattr(obj, "number_of_nodes", lambda: "?")(),
                    getattr(obj, "number_of_edges", lambda: "?")())
        return obj

    def exists(self) -> dict[str, bool]:
        """检查两个图谱快照是否存在。"""
        return {
            "schema_graph": self.schema_graph_path.exists(),
            "lineage_graph": self.lineage_graph_path.exists(),
        }

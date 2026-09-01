"""图算法封装。

提供两类算法：
1. JOIN 路径搜索（基于 NetworkX 最短路径 + Dijkstra）
2. 社区检测（Louvain 优先，缺失时降级为 Girvan-Newman）

JOIN 路径用于 NL2SQL Prompt 组装；
社区检测用于将语义相近的表聚类，辅助召回扩展。

对应ResNet注意力机制：路径权重决定语义聚集区域。
"""
from __future__ import annotations

import logging
from typing import Iterable

import networkx as nx

from fabgraph.models.graph import JoinPath
from fabgraph.utils.exceptions import GraphError, NL2SQLError

logger = logging.getLogger(__name__)

# python-louvain 可选
try:
    import community as community_louvain  # type: ignore

    _HAS_LOUVAIN = True
except ImportError:  # pragma: no cover
    community_louvain = None  # type: ignore
    _HAS_LOUVAIN = False


class JoinPathFinder:
    """JOIN 路径查找器。

    基于表级无向 JOIN 图（由 :func:`schema_graph.to_join_graph` 生成），
    使用 Dijkstra 最短路径寻找表间 JOIN 序列。

    Attributes:
        join_graph: 表级无向图，边含 weight/join_condition。
    """

    def __init__(self, join_graph: nx.Graph) -> None:
        """初始化查找器。

        Args:
            join_graph: 表级无向 JOIN 图。
        """
        self.join_graph = join_graph

    def find_path(
        self, start_table: str, end_table: str, max_hops: int = 3
    ) -> JoinPath:
        """查找两表间的最短 JOIN 路径。

        Args:
            start_table: 起始表名。
            end_table: 终止表名。
            max_hops: 最大跳数限制。

        Returns:
            :class:`JoinPath` 模型。

        Raises:
            NL2SQLError: 起止表不存在或无可达路径。
        """
        start = self._resolve_table_node(start_table)
        end = self._resolve_table_node(end_table)
        if start not in self.join_graph:
            raise NL2SQLError(f"起始表不在 JOIN 图中: {start_table}")
        if end not in self.join_graph:
            raise NL2SQLError(f"终止表不在 JOIN 图中: {end_table}")
        if start == end:
            return JoinPath(
                start_table=start_table, end_table=end_table,
                path=[start_table], join_conditions=[], total_weight=0.0,
            )
        try:
            path_nodes = nx.shortest_path(
                self.join_graph, source=start, target=end,
                weight="weight",
            )
        except nx.NodeNotFound as e:
            raise NL2SQLError(f"JOIN 路径节点不存在: {e}") from e
        except nx.NetworkXNoPath as e:
            raise NL2SQLError(
                f"表 {start_table} 与 {end_table} 之间无可达 JOIN 路径"
            ) from e
        if len(path_nodes) - 1 > max_hops:
            raise NL2SQLError(
                f"JOIN 路径超过最大跳数 {max_hops}: 实际 {len(path_nodes) - 1} 跳"
            )
        return self._build_join_path(start_table, end_table, path_nodes)

    def find_multi_table_path(
        self, tables: list[str], max_hops: int = 3
    ) -> list[JoinPath]:
        """查找多表连通所需的 JOIN 路径集合。

        以 ``tables[0]`` 为锚点，依次连接其余表。

        Args:
            tables: 需连通的表名列表（>=2）。
            max_hops: 每段路径最大跳数。

        Returns:
            JoinPath 列表，长度 = len(tables) - 1。
        """
        if len(tables) < 2:
            return []
        paths: list[JoinPath] = []
        connected = {tables[0]}
        remaining = list(tables[1:])
        while remaining:
            path = self._find_nearest(connected, remaining, max_hops)
            if path is None:
                raise NL2SQLError(
                    f"无法连通表集合: 已连通 {connected} 待连 {remaining}"
                )
            paths.append(path)
            connected.add(path.end_table)
            remaining.remove(path.end_table)
        return paths

    def _find_nearest(
        self,
        connected: set[str],
        remaining: list[str],
        max_hops: int,
    ) -> JoinPath | None:
        """从已连通集合中找一条最短路径连接到 remaining 中任一表。"""
        best: JoinPath | None = None
        for src in connected:
            for dst in remaining:
                try:
                    p = self.find_path(src, dst, max_hops=max_hops)
                except NL2SQLError:
                    continue
                if best is None or p.total_weight < best.total_weight:
                    best = p
        return best

    def _build_join_path(
        self,
        start_table: str,
        end_table: str,
        path_nodes: list[str],
    ) -> JoinPath:
        """将节点序列组装为 :class:`JoinPath`。"""
        path_names: list[str] = []
        conditions: list[str] = []
        total_weight = 0.0
        for i, node in enumerate(path_nodes):
            path_names.append(self._node_to_table_name(node))
            if i > 0:
                edge = self.join_graph[path_nodes[i - 1]][node]
                total_weight += float(edge.get("weight", 1.0))
                cond = edge.get("join_condition", "")
                if cond:
                    conditions.append(cond)
        return JoinPath(
            start_table=start_table, end_table=end_table,
            path=path_names, join_conditions=conditions,
            total_weight=total_weight,
        )

    def _resolve_table_node(self, table_name: str) -> str:
        """解析表名为图中的节点 id。

        兼容节点 id 形如 ``table:LOT_HISTORY`` 或纯表名 ``LOT_HISTORY``。
        """
        if table_name in self.join_graph:
            return table_name
        prefixed = f"table:{table_name}"
        if prefixed in self.join_graph:
            return prefixed
        # 大小写兼容
        upper = table_name.upper()
        for n in self.join_graph.nodes:
            if n.upper() == upper or n.upper() == f"TABLE:{upper}":
                return n
        return table_name  # 让上游报错

    @staticmethod
    def _node_to_table_name(node: str) -> str:
        """节点 id 转纯表名。"""
        if node.startswith("table:"):
            return node[len("table:"):]
        return node


# ---------------- 社区检测 ----------------


def detect_communities(
    graph: nx.Graph,
    method: str = "auto",
    resolution: float = 1.0,
) -> dict[str, int]:
    """社区检测：将节点划分为语义相近的簇。

    Args:
        graph: 无向图（推荐表级 JOIN 图或 Lineage 投影）。
        method: ``auto`` | ``louvain`` | ``girvan_newman``。
        resolution: Louvain 分辨率（越大社区越多）。

    Returns:
        node_id -> community_id 映射。

    Raises:
        GraphError: 指定方法不可用或图不适用。
    """
    if graph.number_of_nodes() == 0:
        return {}
    if method == "auto":
        method = "louvain" if _HAS_LOUVAIN else "girvan_newman"
    if method == "louvain":
        if not _HAS_LOUVAIN:
            logger.warning("Louvain 不可用，降级为 Girvan-Newman")
            return _girvan_newman_communities(graph)
        return _louvain_communities(graph, resolution)
    if method == "girvan_newman":
        return _girvan_newman_communities(graph)
    raise GraphError(f"不支持的社区检测方法: {method}")


def _louvain_communities(
    graph: nx.Graph, resolution: float
) -> dict[str, int]:
    """Louvain 社区检测（需 python-louvain）。"""
    assert community_louvain is not None
    # 转无向简单图
    simple = nx.Graph(graph)
    partition = community_louvain.best_partition(simple, resolution=resolution)
    logger.info(
        "Louvain 社区检测: %d 节点 -> %d 社区",
        len(partition), len(set(partition.values())),
    )
    return dict(partition)


def _girvan_newman_communities(graph: nx.Graph) -> dict[str, int]:
    """Girvan-Newman 社区检测（NetworkX 内置，无需额外依赖）。

    启发式：取使模块度增益最大的切分层数。
    """
    simple = nx.Graph(graph)
    if simple.number_of_edges() == 0:
        return {n: i for i, n in enumerate(simple.nodes())}
    comp = nx.community.girvan_newman(simple)  # type: ignore[attr-defined]
    best_partition: dict[str, int] = {}
    best_modularity = -1.0
    # 取前若干层，挑模块度最高者
    for i, communities in enumerate(comp):
        if i >= 8:
            break
        partition = {}
        for cid, comm in enumerate(communities):
            for node in comm:
                partition[node] = cid
        try:
            mod = nx.algorithms.community.quality.modularity(simple, communities)
        except Exception:
            mod = -1.0
        if mod > best_modularity:
            best_modularity = mod
            best_partition = partition
    if not best_partition:
        best_partition = {n: 0 for n in simple.nodes()}
    logger.info(
        "Girvan-Newman 社区检测: %d 节点 -> %d 社区 (模块度=%.4f)",
        len(best_partition), len(set(best_partition.values())), best_modularity,
    )
    return best_partition


def get_community_members(
    partition: dict[str, int], community_id: int
) -> list[str]:
    """返回指定社区的成员节点 id 列表。"""
    return [n for n, cid in partition.items() if cid == community_id]


def list_communities(partition: dict[str, int]) -> dict[int, list[str]]:
    """按社区 id 分组节点。"""
    out: dict[int, list[str]] = {}
    for node, cid in partition.items():
        out.setdefault(cid, []).append(node)
    return out

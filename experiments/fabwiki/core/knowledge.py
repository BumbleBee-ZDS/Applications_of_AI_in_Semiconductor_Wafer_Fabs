"""知识包运行时：扫描 knowledge/ 下所有 .md，解析 frontmatter，构建索引与血缘图。

核心能力：
- 加载/解析所有知识点
- 解析 markdown 中的相对路径链接，构建 networkx 有向图（节点=知识点，边=链接）
- 按 type/tag/关键词过滤、读取单文件、获取某表的 N 跳关联知识（血缘上下游）

链接解析约定：
- 行内链接：`[标题](../wiki/tables/WIP_LOT.md)` 或 `[标题](tables/WIP_LOT.md)`（相对 knowledge/）
- 自动血缘：节点 frontmatter 中 `related` 字段列出的相对路径
- 编译器生成的 lineage 文件用自动血缘字段承载表间上下游
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter
import networkx as nx

import config


@dataclass
class KnowledgeNode:
    """单个知识点（一个 .md 文件）。"""
    path: Path                 # 相对 knowledge/ 的路径，如 wiki/tables/WIP_LOT.md
    title: str
    type: str
    resource: str
    tags: list[str] = field(default_factory=list)
    confidence: str = field(default="unknown")
    updated: str = field(default="")
    body: str = field(default="")
    frontmatter: dict = field(default_factory=dict)
    links: list[str] = field(default_factory=list)   # 解析出的目标知识点路径


class KnowledgeBase:
    """内存中的知识包索引 + 血缘有向图。"""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or config.KNOWLEDGE_DIR)
        self.nodes: dict[str, KnowledgeNode] = {}     # relpath -> Node
        self.by_type: dict[str, list[str]] = {}
        self.graph: nx.DiGraph = nx.DiGraph()
        self.load()

    # ------------------------------------------------------------------
    # 加载与解析
    # ------------------------------------------------------------------
    def _rel(self, p: Path) -> str:
        return p.resolve().relative_to(self.root.resolve()).as_posix()

    def load(self) -> None:
        """扫描并重建整个索引与图（幂等，可重复调用）。"""
        self.nodes.clear()
        self.by_type.clear()
        self.graph = nx.DiGraph()

        for md in self.root.rglob("*.md"):
            rel = self._rel(md)
            try:
                post = frontmatter.loads(md.read_text(encoding="utf-8"))
            except Exception:
                continue   # 解析失败的跳过，不阻塞整体
            meta = post.metadata or {}
            node = KnowledgeNode(
                path=rel,
                title=meta.get("title", md.stem),
                type=meta.get("type", "unknown"),
                resource=meta.get("resource", md.stem),
                tags=list(meta.get("tags", [])),
                confidence=meta.get("confidence", "unknown"),
                updated=meta.get("updated", ""),
                body=post.content,
                frontmatter=meta,
            )
            node.links = self._parse_links(post.content, md) + self._parse_related(meta)
            node.links = [l for l in dict.fromkeys(node.links)]   # 去重保序
            self.nodes[rel] = node
            self.by_type.setdefault(node.type, []).append(rel)

        # 全部节点就位后再过滤链接（避免处理顺序导致漏链）
        for rel, node in self.nodes.items():
            node.links = [l for l in node.links if l in self.nodes]

        self._build_graph()

    def _parse_links(self, content: str, md: Path) -> list[str]:
        """从正文解析 `[t](相对路径)` 链接，返回目标知识点相对路径。"""
        links: list[str] = []
        for m in re.finditer(r"\]\(([^)]+\.md)\)", content):
            target = m.group(1)
            target = target.split("#")[0]
            target_path = (md.parent / target).resolve()
            try:
                rel = target_path.relative_to(self.root.resolve()).as_posix()
            except ValueError:
                continue
            if rel:   # 过滤有效性放到节点全部就位后统一做
                links.append(rel)
        return links

    def _parse_related(self, meta: dict) -> list[str]:
        """解析 frontmatter 中 `related` 字段（可含相对 knowledge/ 的路径）。"""
        out: list[str] = []
        root = self.root.resolve()
        for item in meta.get("related", []) or []:
            p = (self.root / str(item)).resolve()
            try:
                rel = p.relative_to(root).as_posix()
            except ValueError:
                continue
            out.append(rel)
        return out

    def _build_graph(self) -> None:
        for rel in self.nodes:
            self.graph.add_node(rel)
        for src, node in self.nodes.items():
            for dst in node.links:
                if dst in self.nodes:
                    self.graph.add_edge(src, dst)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def all(self, type_: str | None = None,
            tag: str | None = None,
            kw: str | None = None) -> list[KnowledgeNode]:
        """按 type/tag/关键词过滤，返回排序后的节点列表。"""
        res = []
        for rel, node in self.nodes.items():
            if type_ and node.type != type_:
                continue
            if tag and tag not in node.tags:
                continue
            if kw and kw.lower() not in (node.title + node.body + node.resource).lower():
                continue
            res.append(node)
        res.sort(key=lambda n: n.path)
        return res

    def get(self, rel: str) -> KnowledgeNode | None:
        return self.nodes.get(rel)

    def types(self) -> list[str]:
        return sorted(self.by_type.keys())

    def tags(self) -> list[str]:
        s: set[str] = set()
        for n in self.nodes.values():
            s.update(n.tags)
        return sorted(s)

    def neighbors(self, rel: str, hops: int = 1,
                  direction: str = "both") -> dict[str, list[str]]:
        """某知识点的 N 跳关联（血缘上下游），direction: both/in/out。"""
        if rel not in self.nodes:
            return {"upstream": [], "downstream": [], "linked": []}
        g = self.graph
        up: set[str] = set()
        if direction in ("both", "in"):
            for _ in range(hops):
                preds = {p for n in (up | {rel}) if n in g for p in g.predecessors(n)}
                up |= preds - {rel}
        down: set[str] = set()
        if direction in ("both", "out"):
            for _ in range(hops):
                succs = {s for n in (down | {rel}) if n in g for s in g.successors(n)}
                down |= succs - {rel}
        return {
            "upstream": sorted(up - down),
            "downstream": sorted(down - up),
            "linked": sorted((up & down)),
        }

    def stats(self) -> dict[str, int]:
        conf: dict[str, int] = {}
        types: dict[str, int] = {}
        for n in self.nodes.values():
            conf[n.confidence] = conf.get(n.confidence, 0) + 1
            types[n.type] = types.get(n.type, 0) + 1
        return {"nodes": len(self.nodes), "edges": self.graph.number_of_edges(),
                "conf": conf, "types": types}

    def locate_tables(self, keywords: list[str]) -> list[KnowledgeNode]:
        """按关键词定位最相关的表知识点（Text2SQL 第 1 步）。

        优先匹配表名/资源名，其次匹配标题/标签/正文。
        """
        scored: dict[str, float] = {}
        base = [kw.lower() for kw in keywords if kw]
        if not base:
            base = [""]
        for rel, node in self.nodes.items():
            if node.type != "Table":
                continue
            hay = (node.resource + " " + node.title + " " +
                   " ".join(node.tags) + " " + node.body).lower()
            score = 0.0
            for kw in base:
                if kw and kw in hay:
                    # 资源名（表名）命中优先，其次其他文本
                    score += 3.0 if kw in node.resource.lower() else 1.0
                else:
                    score += 0.1
            scored[rel] = score
        ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
        return [self.nodes[rel] for rel, _ in ranked[:5] if self.nodes[rel]]

    def locate_columns(self, keywords: list[str],
                       table_filter: list[str] | None = None) -> list[KnowledgeNode]:
        """按关键词定位最相关的字段知识点（Column 类型）。

        - keywords: 关键词列表
        - table_filter: 可选，仅在指定表的字段中搜索（表名列表）
        """
        scored: dict[str, float] = {}
        base = [kw.lower() for kw in keywords if kw]
        if not base:
            base = [""]
        for rel, node in self.nodes.items():
            if node.type != "Column":
                continue
            # 表过滤
            if table_filter:
                tbl = node.resource.split(".")[0] if "." in node.resource else ""
                if tbl not in table_filter:
                    continue
            hay = (node.resource + " " + node.title + " " +
                   " ".join(node.tags) + " " + node.body).lower()
            score = 0.0
            for kw in base:
                if kw and kw in hay:
                    # 字段名命中优先（resource 中包含字段名）
                    score += 4.0 if kw in node.resource.lower().split(".")[-1] else (
                        2.0 if kw in node.resource.lower() else 1.0
                    )
                else:
                    score += 0.1
            scored[rel] = score
        ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
        return [self.nodes[rel] for rel, _ in ranked[:10] if self.nodes[rel]]

    def columns_of_table(self, table_name: str) -> list[KnowledgeNode]:
        """获取某张表的所有 Column 级知识点。"""
        result = []
        for rel, node in self.nodes.items():
            if node.type == "Column" and node.resource.startswith(f"{table_name}."):
                result.append(node)
        result.sort(key=lambda n: n.resource)
        return result
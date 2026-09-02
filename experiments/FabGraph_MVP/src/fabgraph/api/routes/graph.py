"""图谱路由：Schema Graph / Lineage Graph / 社区检测 / JOIN 路径。"""
from __future__ import annotations

from typing import Any

import networkx as nx
from fastapi import APIRouter, Depends, Query

from fabgraph.api.deps import get_build_result
from fabgraph.graph.graph_algorithms import (
    JoinPathFinder,
    detect_communities,
    list_communities,
)
from fabgraph.graph.graph_utils import (
    to_join_graph,
    project_lineage_to_undirected,
)
from fabgraph.graph.lineage_graph import (
    get_downstream_tables,
    get_hyperedges,
    get_upstream_tables,
)
from fabgraph.models.graph import EdgeType, NodeType
from fabgraph.service.graph_builder import BuildResult

router = APIRouter()


@router.get("/schema/summary")
async def schema_summary(
    result: BuildResult = Depends(get_build_result),
) -> dict[str, Any]:
    """Schema Graph 摘要。"""
    g = result.schema_graph
    return {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "tables": result.table_count,
        "join_edges": result.join_graph.number_of_edges(),
    }


@router.get("/schema/nodes")
async def schema_nodes(
    node_type: str | None = Query(None, description="过滤节点类型"),
    result: BuildResult = Depends(get_build_result),
) -> list[dict[str, Any]]:
    """返回 Schema Graph 节点列表。"""
    g = result.schema_graph
    nodes: list[dict[str, Any]] = []
    for nid, data in g.nodes(data=True):
        nt = data.get("node_type")
        if nt is None:
            continue
        if node_type and nt.value != node_type:
            continue
        nodes.append({
            "id": nid,
            "type": nt.value,
            "name": data.get("name", ""),
            "description": data.get("description", ""),
        })
    return nodes


@router.get("/schema/edges")
async def schema_edges(
    edge_type: str | None = Query(None, description="过滤边类型"),
    result: BuildResult = Depends(get_build_result),
) -> list[dict[str, Any]]:
    """返回 Schema Graph 边列表。"""
    g = result.schema_graph
    edges: list[dict[str, Any]] = []
    for u, v, data in g.edges(data=True):
        et = data.get("edge_type")
        if et is None:
            continue
        if edge_type and et.value != edge_type:
            continue
        edges.append({
            "source": u, "target": v,
            "type": et.value, "weight": data.get("weight", 1.0),
        })
    return edges


@router.get("/lineage/summary")
async def lineage_summary(
    result: BuildResult = Depends(get_build_result),
) -> dict[str, Any]:
    """Lineage Graph 摘要。"""
    g = result.lineage_graph
    hypers = get_hyperedges(g)
    return {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "hyperedges": len(hypers),
    }


@router.get("/lineage/hyperedges")
async def lineage_hyperedges(
    result: BuildResult = Depends(get_build_result),
) -> list[dict[str, Any]]:
    """返回 Lineage Graph 全部超边。"""
    hypers = get_hyperedges(result.lineage_graph)
    return [
        {
            "edge_id": h.edge_id,
            "procedure": h.procedure_name,
            "source_tables": h.source_tables,
            "target_tables": h.target_tables,
        }
        for h in hypers.values()
    ]


@router.get("/lineage/upstream/{table_name}")
async def lineage_upstream(
    table_name: str,
    result: BuildResult = Depends(get_build_result),
) -> dict[str, Any]:
    """返回指定表的上游表列表。"""
    tables = get_upstream_tables(result.lineage_graph, table_name)
    return {"table": table_name, "upstream": tables}


@router.get("/lineage/downstream/{table_name}")
async def lineage_downstream(
    table_name: str,
    result: BuildResult = Depends(get_build_result),
) -> dict[str, Any]:
    """返回指定表的下游表列表。"""
    tables = get_downstream_tables(result.lineage_graph, table_name)
    return {"table": table_name, "downstream": tables}


@router.get("/communities")
async def communities(
    graph: str = Query("schema", description="schema | lineage"),
    method: str = Query("auto", description="auto | louvain | girvan_newman"),
    result: BuildResult = Depends(get_build_result),
) -> dict[str, Any]:
    """社区检测。"""
    if graph == "lineage":
        ug = project_lineage_to_undirected(result.lineage_graph)
    else:
        ug = to_join_graph(result.schema_graph)
    partition = detect_communities(ug, method=method)
    grouped = list_communities(partition)
    return {
        "total_nodes": len(partition),
        "total_communities": len(grouped),
        "communities": {
            str(cid): members for cid, members in grouped.items()
        },
    }


@router.get("/join-path")
async def join_path(
    start: str = Query(..., description="起始表名"),
    end: str = Query(..., description="终止表名"),
    max_hops: int = Query(3, ge=1, le=5),
    result: BuildResult = Depends(get_build_result),
) -> dict[str, Any]:
    """查找两表间的 JOIN 路径。"""
    finder = JoinPathFinder(result.join_graph)
    path = finder.find_path(start, end, max_hops=max_hops)
    return {
        "start": path.start_table,
        "end": path.end_table,
        "path": path.path,
        "join_conditions": path.join_conditions,
        "total_weight": path.total_weight,
    }

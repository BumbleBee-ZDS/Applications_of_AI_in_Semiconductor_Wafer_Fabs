"""语义检索路由。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from fabgraph.api.deps import get_semantic_service
from fabgraph.service.semantic_service import SemanticSearchService

router = APIRouter()


class SearchRequest(BaseModel):
    """语义检索请求。"""

    question: str = Field(..., description="自然语言问题")
    top_k: int = Field(5, ge=1, le=50)
    expand: bool = Field(True, description="是否启用图谱扩展")


@router.post("/search")
async def semantic_search(
    req: SearchRequest,
    service: SemanticSearchService = Depends(get_semantic_service),
) -> dict[str, Any]:
    """语义检索表/字段。"""
    results = service.search(
        req.question, top_k=req.top_k, expand=req.expand
    )
    return {
        "question": req.question,
        "total": len(results),
        "results": [_result_dict(r) for r in results],
    }


@router.post("/search-tables")
async def search_tables(
    req: SearchRequest,
    service: SemanticSearchService = Depends(get_semantic_service),
) -> dict[str, Any]:
    """仅检索表级结果。"""
    results = service.search_tables(
        req.question, top_k=req.top_k, expand=False
    )
    return {
        "question": req.question,
        "total": len(results),
        "results": [_result_dict(r) for r in results],
    }


@router.post("/reindex")
async def reindex(
    service: SemanticSearchService = Depends(get_semantic_service),
) -> dict[str, Any]:
    """重建向量索引。"""
    n = service.index_metadata()
    return {"status": "ok", "indexed_items": n}


def _result_dict(r) -> dict[str, Any]:
    """SearchResult 序列化。"""
    return {
        "item_id": r.item_id,
        "table_name": r.table_name,
        "column_name": r.column_name,
        "node_type": r.node_type.value,
        "score": round(r.score, 4),
        "expanded_from": r.expanded_from,
        "text": r.item.text if r.item else "",
    }

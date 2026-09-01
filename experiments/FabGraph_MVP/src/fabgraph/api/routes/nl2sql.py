"""NL2SQL 路由：自然语言转 SQL。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from fabgraph.api.deps import get_nl2sql_service, get_sql_analyzer
from fabgraph.models.semantic import NL2SQLRequest
from fabgraph.service.nl2sql_service import NL2SQLService
from fabgraph.service.sql_analyzer import SqlAnalyzerService

router = APIRouter()


class GenerateRequest(BaseModel):
    """NL2SQL 生成请求。"""

    question: str = Field(..., description="自然语言问题")
    top_k: int = Field(5, ge=1, le=20)


@router.post("/generate")
async def generate_sql(
    req: GenerateRequest,
    service: NL2SQLService = Depends(get_nl2sql_service),
) -> dict[str, Any]:
    """生成 SQL。"""
    request = NL2SQLRequest(question=req.question, top_k=req.top_k)
    resp = service.generate(request)
    return {
        "question": resp.question,
        "sql": resp.sql,
        "related_tables": resp.related_tables,
        "join_paths": resp.join_paths,
        "confidence": round(resp.confidence, 4),
        "is_validated": resp.is_validated,
        "mock_mode": resp.mock_mode,
        "context": resp.context,
    }


class AnalyzeRequest(BaseModel):
    """SQL 分析请求。"""

    sql: str = Field(..., description="待分析 SQL 文本")


@router.post("/analyze")
async def analyze_sql(
    req: AnalyzeRequest,
    analyzer: SqlAnalyzerService = Depends(get_sql_analyzer),
) -> dict[str, Any]:
    """分析 SQL，提取语义提示。"""
    hints = analyzer.analyze(req.sql)
    return {
        "sql": req.sql,
        "total_hints": len(hints),
        "hints": [
            {
                "table_name": h.table_name,
                "column_name": h.column_name,
                "hint_type": h.hint_type,
                "hint_value": h.hint_value,
                "confidence": h.confidence,
            }
            for h in hints
        ],
    }


@router.post("/analyze-batch")
async def analyze_batch(
    sqls: list[dict[str, Any]],
    analyzer: SqlAnalyzerService = Depends(get_sql_analyzer),
) -> dict[str, Any]:
    """批量分析 SQL 历史。"""
    hints = analyzer.analyze_batch(sqls)
    # 按 hint_type 聚合统计
    type_counts: dict[str, int] = {}
    for h in hints:
        type_counts[h.hint_type] = type_counts.get(h.hint_type, 0) + 1
    return {
        "total_sqls": len(sqls),
        "total_hints": len(hints),
        "by_type": type_counts,
    }

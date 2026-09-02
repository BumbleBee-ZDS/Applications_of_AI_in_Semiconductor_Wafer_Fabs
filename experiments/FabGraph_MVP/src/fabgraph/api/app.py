"""FastAPI 应用工厂。

负责：
- 创建 FastAPI 实例
- 注册全局异常处理器（FabGraphError -> 结构化 JSON）
- 挂载全部路由
- 启动时初始化元数据与图谱（lifespan）

对应ResNet推理引擎：加载权重 + 注册输出头 + 暴露推理端点。
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fabgraph.api.deps import (
    get_metadata_repo,
    get_build_result,
    reset_dependencies,
)
from fabgraph.config import get_settings
from fabgraph.utils.exceptions import FabGraphError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时预加载元数据与图谱。"""
    settings = get_settings()
    logger.info("FabGraph 启动中 (mock_llm=%s)...", settings.llm.use_mock)
    try:
        # 确保元数据已加载（先建表再查询，避免首次启动时表不存在）
        repo = get_metadata_repo()
        repo.init_db()
        tables = repo.get_tables()
        if not tables:
            logger.info("元数据为空，从 JSON 加载...")
            repo.load_from_json()
        # 预构建图谱
        get_build_result()
        logger.info("FabGraph 启动完成")
    except Exception as e:
        logger.error("启动初始化失败: %s", e)
    yield
    logger.info("FabGraph 关闭")
    reset_dependencies()


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。

    Returns:
        配置完整的 FastAPI 应用。
    """
    settings = get_settings()
    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description="FabGraph MVP — 知识图谱驱动的 NL2SQL 服务",
        lifespan=lifespan,
    )

    # 注册异常处理器
    _register_exception_handlers(app)

    # 挂载路由
    _register_routes(app)

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。"""

    @app.exception_handler(FabGraphError)
    async def handle_fabgraph_error(
        request: Request, exc: FabGraphError
    ) -> JSONResponse:
        """FabGraphError 统一转结构化 JSON。"""
        return JSONResponse(
            status_code=_error_status(exc),
            content=exc.to_dict(),
        )


def _error_status(exc: FabGraphError) -> int:
    """根据异常类型映射 HTTP 状态码。"""
    from fabgraph.utils.exceptions import (
        ConfigError, MetadataError, GraphError,
        SQLAnalysisError, SearchError, EmbeddingError,
        LLMError, NL2SQLError,
    )
    mapping = {
        ConfigError: 500,
        MetadataError: 404,
        GraphError: 500,
        SQLAnalysisError: 422,
        SearchError: 404,
        EmbeddingError: 500,
        LLMError: 502,
        NL2SQLError: 422,
    }
    for cls, code in mapping.items():
        if isinstance(exc, cls):
            return code
    return 500


def _register_routes(app: FastAPI) -> None:
    """挂载全部 API 路由。"""
    from fabgraph.api.routes.metadata import router as metadata_router
    from fabgraph.api.routes.graph import router as graph_router
    from fabgraph.api.routes.search import router as search_router
    from fabgraph.api.routes.nl2sql import router as nl2sql_router

    app.include_router(metadata_router, prefix="/api/metadata", tags=["metadata"])
    app.include_router(graph_router, prefix="/api/graph", tags=["graph"])
    app.include_router(search_router, prefix="/api/search", tags=["search"])
    app.include_router(nl2sql_router, prefix="/api/nl2sql", tags=["nl2sql"])

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        """健康检查端点。"""
        return {"status": "ok"}

import sys

# Windows 控制台 UTF-8 编码，支持 emoji 和中文输出
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from api.endpoints import router, initialize_agent
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理器
    替代 @app.on_event("startup")，确保在 uvicorn reload 模式下也能正确触发
    """
    print("🔧 启动应用生命周期...")
    initialize_agent()
    print("✅ 应用启动完成")
    yield
    print("🔌 应用关闭中...")


app = FastAPI(
    title="Semiconductor Wafer Fab Ontology MVP",
    description="基于 GraphRAG 的晶圆厂根因分析 Agent 系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
async def root():
    """根路径返回欢迎信息"""
    return {
        "message": "Welcome to Wafer Fab Ontology MVP",
        "endpoints": {
            "/investigate": "POST - 启动根因分析调查",
            "/health": "GET - 健康检查",
        },
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

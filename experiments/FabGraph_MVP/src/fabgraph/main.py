"""FabGraph 应用启动入口。

提供：
- ``app``：FastAPI 应用实例（供 ``uvicorn fabgraph.main:app`` 使用）
- :func:`main`：CLI 启动函数（``python -m fabgraph.main``）

对应ResNet推理引擎入口：加载配置 -> 初始化权重 -> 暴露服务。
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# 确保 src 目录在 sys.path 中（直接 ``python main.py`` 时也能导入）
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fabgraph.api.app import create_app  # noqa: E402
from fabgraph.config import get_settings  # noqa: E402

# 创建全局 app 实例（uvicorn 通过模块路径引用）
app = create_app()


def _configure_logging(level: str) -> None:
    """配置根日志器。

    Args:
        level: 日志级别字符串（DEBUG/INFO/WARNING/ERROR）。
    """
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    """CLI 启动入口。

    读取配置后用 uvicorn 启动 FastAPI 应用。
    """
    settings = get_settings()
    _configure_logging(settings.app.log_level)

    logger = logging.getLogger(__name__)
    logger.info(
        "启动 FabGraph: host=%s port=%s debug=%s mock_llm=%s mock_embed=%s",
        settings.app.host, settings.app.port, settings.app.debug,
        settings.llm.use_mock, settings.embedding.use_mock,
    )

    # uvicorn 作为应用内运行器启动，便于共享 app 实例与 lifespan
    import uvicorn

    uvicorn.run(
        "fabgraph.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )


if __name__ == "__main__":
    main()

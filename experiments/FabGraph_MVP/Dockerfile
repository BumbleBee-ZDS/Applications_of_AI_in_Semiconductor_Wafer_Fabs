# FabGraph MVP 多阶段构建镜像
# 基础镜像：Python 3.11 slim
FROM python:3.11-slim AS base

# 设置环境变量，禁用字节码缓存以减小镜像体积，日志实时输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 安装系统依赖（FAISS / sentence-transformers 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 先拷贝依赖描述以利用 Docker 层缓存
COPY pyproject.toml ./
COPY src ./src

# 安装项目依赖（以 editable 方式安装本包）
RUN pip install --upgrade pip && pip install -e ".[dev]"

# 拷贝其余源码与配置
COPY configs ./configs
COPY scripts ./scripts
COPY ui ./ui
COPY data ./data

EXPOSE 8000 8501

# 默认启动 API 服务，UI 通过 docker-compose 单独拉起
CMD ["uvicorn", "fabgraph.main:app", "--host", "0.0.0.0", "--port", "8000"]

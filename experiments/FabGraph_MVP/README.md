# FabGraph MVP

晶圆厂数据资产知识图谱系统 —— 以 **Schema Graph + Lineage Graph** 双图谱为核心，
驱动语义检索与 NL2SQL。

> 设计隐喻：整套系统参照 ResNet 架构 —— 元数据作为输入特征，SQL 分析器作为残差块
> 逐层注入语义信号，图谱作为跨层连接避免语义孤岛，最终 NL2SQL 作为输出头产出 SQL。

## 功能特性

- **元数据管理**：表 / 字段 / 存储过程 / SQL 历史，SQLite 持久化
- **Schema Graph**：表 - 字段 - FK - 推断 JOIN 关系图
- **Lineage Graph**：过程读/写表构成的数据血缘超图
- **语义检索**：向量近邻 + 图谱 1-hop 扩展召回
- **NL2SQL**：检索增强 + JOIN 路径约束 + LLM 生成 Oracle SQL
- **图算法**：JOIN 最短路径、社区检测（Louvain / Girvan-Newman）
- **Mock 兜底**：无 LLM API Key / 无嵌入模型时自动降级，开箱可跑

## 架构分层

```
api        -> FastAPI 路由层（请求校验 + service 调用 + 结构化 JSON）
service    -> 业务编排层（语义检索 / NL2SQL / 图谱构建 / SQL 分析）
repository -> 数据访问层（SQLite 元数据 / pickle 图谱 / FAISS 向量）
graph      -> 图谱构建与算法（NetworkX）
models     -> Pydantic 数据模型
utils      -> LLM 客户端 / 嵌入客户端 / SQL 解析器 / 异常层级
```

依赖方向：`api -> service -> repository / graph -> models / utils`，禁止逆向。

## 目录结构

```
FabGraph_MVP/
├── configs/settings.yaml      # 配置（${VAR:default} 占位符由 .env 展开）
├── data/
│   ├── mock_oracle/           # 仿真晶圆厂元数据 JSON
│   ├── fabgraph.db            # SQLite 元数据库（运行时生成）
│   ├── schema_graph.pkl       # Schema Graph 快照
│   ├── lineage_graph.pkl      # Lineage Graph 快照
│   └── faiss_index/           # FAISS 向量索引
├── scripts/init_mock_data.py  # 生成仿真元数据
├── src/fabgraph/
│   ├── main.py                # FastAPI 启动入口
│   ├── config.py              # YAML + .env 配置加载
│   ├── api/                   # FastAPI 应用 + 路由 + 依赖注入
│   ├── service/               # 业务编排服务
│   ├── repository/            # 元数据 / 图谱 / 向量仓储
│   ├── graph/                 # 图谱构建与算法
│   ├── models/                # schema / graph / semantic 模型
│   └── utils/                 # LLM / 嵌入 / SQL 解析 / 异常
├── ui/streamlit_app/
│   ├── app.py                 # Streamlit 入口
│   ├── services.py            # 缓存的 service 实例
│   ├── graph_viz.py           # pyvis 可视化组件
│   ├── page_metadata.py       # 元数据浏览
│   ├── page_graph.py          # 图谱可视化
│   ├── page_search.py         # 语义检索
│   ├── page_nl2sql.py         # NL2SQL
│   └── page_sql_analyzer.py   # SQL 分析
├── tests/                     # pytest 测试套件
├── Dockerfile / docker-compose.yml
└── pyproject.toml
```

## 快速开始

### 环境要求

- Python >= 3.11
- 推荐 venv / conda 隔离环境

### 安装

```bash
# 克隆后进入项目根目录
pip install -e ".[dev]"
```

### 配置

编辑 `.env`（参考 `.env.example`）：

```dotenv
# LLM：留空则自动启用 mock 模式
DEEPSEEK_API_KEY=sk-xxx
USE_MOCK_LLM=false          # false=真实 LLM, true=Mock 兜底
USE_MOCK_EMBEDDINGS=true    # 无 sentence-transformers 时保持 true
```

`configs/settings.yaml` 中所有 `${VAR:default}` 占位符优先取环境变量，
缺失时使用默认值，无需修改即可运行。

### 生成仿真数据

```bash
python scripts/init_mock_data.py
```

产出 `data/mock_oracle/{tables,columns,procedures,sql_history}.json`，
含 8 张核心表、混合命名风格字段、过程血缘与 50+ 条历史 SQL。

### 启动 API 服务

```bash
# 方式一：uvicorn 直接启动
uvicorn fabgraph.main:app --host 0.0.0.0 --port 8000 --reload

# 方式二：模块入口
python -m fabgraph.main
```

启动后访问：
- API 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

### 启动 Streamlit UI

```bash
streamlit run ui/streamlit_app/app.py
```

访问 <http://localhost:8501>，侧边栏切换：
- 元数据浏览
- 图谱可视化（Schema / JOIN / Lineage / 社区检测）
- 语义检索
- NL2SQL
- SQL 分析

### Docker 部署

```bash
docker-compose up --build
```

同时拉起 API（8000）与 UI（8501）。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/health` | 健康检查 |
| GET  | `/api/metadata/tables` | 表列表 |
| GET  | `/api/metadata/tables/{name}` | 表详情（含字段） |
| GET  | `/api/metadata/procedures` | 存储过程列表 |
| GET  | `/api/metadata/sql-history` | 历史 SQL |
| POST | `/api/metadata/reload` | 重新加载元数据 |
| GET  | `/api/graph/schema/summary` | Schema Graph 摘要 |
| GET  | `/api/graph/schema/nodes` | Schema Graph 节点 |
| GET  | `/api/graph/schema/edges` | Schema Graph 边 |
| GET  | `/api/graph/lineage/summary` | Lineage Graph 摘要 |
| GET  | `/api/graph/lineage/hyperedges` | 血缘超边列表 |
| GET  | `/api/graph/lineage/upstream/{table}` | 上游表 |
| GET  | `/api/graph/lineage/downstream/{table}` | 下游表 |
| GET  | `/api/graph/communities` | 社区检测 |
| GET  | `/api/graph/join-path` | JOIN 路径查找 |
| POST | `/api/search/search` | 语义检索 |
| POST | `/api/search/search-tables` | 仅表级检索 |
| POST | `/api/search/reindex` | 重建向量索引 |
| POST | `/api/nl2sql/generate` | 生成 SQL |
| POST | `/api/nl2sql/analyze` | 分析单条 SQL |
| POST | `/api/nl2sql/analyze-batch` | 批量分析 SQL |

所有 `FabGraphError` 子类异常统一返回结构化 JSON，HTTP 状态码按异常类型映射
（404 / 422 / 500 / 502）。

## 测试

```bash
pytest                          # 全量
pytest tests/test_graph_algorithms.py  # 单模块
pytest --cov=fabgraph           # 覆盖率
```

测试使用 `tmp_path` fixture 隔离数据库与图谱文件，不污染仓库目录。
LLM 与嵌入客户端在测试中均走 Mock 路径。

## 关键设计

### 双图谱

- **Schema Graph**（`MultiDiGraph`）：表 -> 字段（`has_column`）、
  字段 <-> 字段（`foreign_key` / `join_inferred`）。投影为表级无向 JOIN 图
  供最短路径算法使用。
- **Lineage Graph**（`MultiDiGraph`）：过程读/写表（`reads` / `writes`），
  过程作为超边连接输入/输出表集合；同时推导表 -> 表的 `lineage` 边。

### 检索增强

`SemanticSearchService` 先做向量近邻召回，再借 Schema Graph 做一跳扩展
（命中表的同表字段获得 0.7x 分数加成），避免纯向量相似度漏召远端语义相关字段。

### NL2SQL 编排

1. 语义检索召回相关表
2. `JoinPathFinder` 在 JOIN 图上计算多表连通路径
3. 组装 Schema 上下文（DDL + JOIN 条件）
4. LLM 生成 Oracle SQL
5. `SqlParser` 校验语法合法性

### ResNet 隐喻

| ResNet 概念 | FabGraph 对应 |
|-------------|---------------|
| 输入特征 | 原始元数据（表/字段/过程） |
| 残差块 | SQL 分析器，逐条 SQL 注入语义信号 |
| 跨层连接 | 图谱传播表间语义与血缘 |
| 全局池化 | 依赖注入的共享单例 |
| 输出头 | NL2SQL / 检索结果 |
| 注意力 | JOIN 路径权重 / 社区聚类 |

## 配置参考

完整配置见 `configs/settings.yaml`，关键项：

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `llm.use_mock` | true | 无 API Key 时使用预设响应 |
| `llm.provider` | deepseek | openai / deepseek |
| `embedding.use_mock` | true | 无模型时用 TF-IDF 兜底 |
| `embedding.dimension` | 384 | 嵌入维度（需与模型一致） |
| `nl2sql.max_join_hops` | 3 | JOIN 路径最大跳数 |
| `search.hop_expansion` | 1 | 图谱扩展跳数 |
| `app.port` | 8000 | API 端口 |

## License

MIT

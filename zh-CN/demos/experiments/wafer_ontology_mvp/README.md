# 🔬 半导体晶圆厂 Ontology MVP

基于 **GraphRAG** 和 **LangGraph** 构建的半导体晶圆厂虚拟工厂（Virtual Fab）根因分析（RCA）Agent 系统。核心理念借鉴自 **Palantir Ontology**：将分散的数据抽象为业务对象（Object）、链接（Link）和动作（Action），让 LLM Agent 在语义层上进行推理，而非直接操作底层数据。

## 🎯 核心目标

- **语义抽象**：将晶圆厂数据建模为业务实体（Lot、Wafer、Equipment 等）
- **图推理**：通过知识图谱进行多跳推理和关系发现
- **智能分析**：LLM Agent 自主规划调查路径，定位质量问题根因
- **可操作**：支持直接执行业务动作（如 Hold 批次）

## 🧠 理论基础

### 1. Palantir Ontology 概念

| 概念 | 定义 | 本项目实现 |
|------|------|-----------|
| **Object** | 业务实体，如批次、晶圆、设备 | `Lot`, `Wafer`, `Equipment`, `ProcessStep`, `Defect` |
| **Link** | 实体间的语义关系 | `CONTAINS`, `PROCESSED_ON`, `HAS_DEFECT` 等 |
| **Action** | 可执行的业务操作 | `hold_lot_action` |
| **Ontology Layer** | 统一的语义抽象层 | NetworkX + SQLite 组合存储 |

### 2. GraphRAG（图增强检索增强生成）

```
用户查询 → LLM 分析 → 图检索（知识关联）→ 属性查询（详细数据）→ 综合推理 → 最终结论
```

### 3. ReAct 循环（Reasoning + Acting）

本项目使用 **LangGraph** 实现 ReAct 循环：

```
[Agent Node] → 思考下一步行动 → [Router] → 判断是否调用工具
    ↑                                      ↓
    └───────────────────────────────── [Tool Node] → 执行工具并返回结果
```

## 🏗️ 技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户界面 (Flask)                           │
│                   http://localhost:5000/                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     聊天界面 / 可视化                         │    │
│  └──────────────────────────────────────┬──────────────────────┘    │
└─────────────────────────────────────────┼───────────────────────────┘
                                          │ HTTP 请求
                                          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       API 层 (FastAPI)                             │
│                   http://localhost:8000/                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  /health        │  │  /investigate   │  │  /graph             │ │
│  │  健康检查       │  │  启动 RCA 调查  │  │  导出图结构         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent 层 (LangGraph)                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐  │    │
│  │  │ Agent    │───▶│ Router   │───▶│ Tool Execution       │  │    │
│  │  │ Node     │◀───│          │◀───│ Node                 │  │    │
│  │  │ (LLM     │    │ (判断    │    │ (执行 query_ontology │  │    │
│  │  │ 推理)    │    │ 下一步)  │    │    _graph 等工具)     │  │    │
│  │  └──────────┘    └──────────┘    └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     Ontology 层 (NetworkX + SQLite)                │
│                                                                     │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │     NetworkX DiGraph        │  │        SQLite Database      │  │
│  │  - 存储 Object 间的 Link   │  │  - 存储 Object 的属性        │  │
│  │  - 支持多跳图遍历查询       │  │  - Lot, Wafer, Equipment... │  │
│  │  - 58 个节点 / 111 条边    │  │  - 通过 SQLModel ORM 访问   │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.11+ | 核心开发语言 |
| 后端框架 | FastAPI | ^0.115.0 | RESTful API 服务 |
| 前端框架 | Flask | ^3.0.0 | Web 界面 |
| 图存储 | NetworkX | ^3.3 | 内存图数据库（替代 Neo4j） |
| 关系存储 | SQLite + SQLModel | ^0.0.16 | 对象属性存储 |
| Agent 框架 | LangGraph | ^0.2.0 | ReAct 循环编排 |
| LLM 集成 | LangChain | ^0.3.0 | LLM 工具调用 |
| LLM 模型 | DeepSeek | - | 通过 OpenAI 兼容 API 访问 |
| 配置管理 | Pydantic Settings | ^2.5.0 | 环境变量加载 |

## 📦 安装与启动

### 环境要求

- Python 3.11+
- 已安装 `pip` 或 `poetry`

### 安装依赖

```bash
# 进入项目目录
cd wafer_ontology_mvp

# 方式一：使用 pip
pip install fastapi uvicorn sqlmodel networkx langchain langchain-openai langgraph python-dotenv pydantic pydantic-settings tenacity flask requests

# 方式二：使用 poetry
poetry install
```

### 配置环境变量

编辑 `.env` 文件，配置 LLM API：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# FastAPI 配置（可选）
HOST=0.0.0.0
PORT=8000
```

### 启动服务

**方式一：分别启动（开发调试）**

```bash
# 终端 1：启动 FastAPI 后端
python src/main.py

# 终端 2：启动 Flask 前端
python web/app.py
```

**方式二：使用 Poetry（推荐）**

```bash
# 启动后端
poetry run python src/main.py

# 启动前端（新终端）
poetry run python web/app.py
```

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| FastAPI 后端 | http://localhost:8000 | API 接口 |
| Flask 前端 | http://localhost:5000 | Web 界面 |
| API 文档 | http://localhost:8000/docs | Swagger UI |

## 📊 Ontology Schema 定义

### Object Types（对象类型）

#### Lot（批次）

| 字段 | 类型 | 说明 |
|------|------|------|
| `lot_id` | str | 批次唯一标识，如 "Lot-W80" |
| `product_name` | str | 产品名称，如 "14nm-FinFET" |
| `current_yield` | float | 当前良率，0-1 之间 |
| `status` | str | 状态：RUNNING / HOLD / COMPLETED |
| `create_time` | datetime | 创建时间 |

#### Wafer（晶圆）

| 字段 | 类型 | 说明 |
|------|------|------|
| `wafer_id` | str | 晶圆唯一标识 |
| `slot` | int | 在批次中的槽位 |
| `parent_lot_id` | str | 所属批次 ID |
| `defect_count` | int | 缺陷数量 |
| `status` | str | 状态 |

#### Equipment（设备）

| 字段 | 类型 | 说明 |
|------|------|------|
| `eq_id` | str | 设备唯一标识，如 "ETCH-A03" |
| `type` | str | 设备类型：Etch / CVD / Lithography / CMP |
| `status` | str | 状态：RUNNING / WARNING / DOWN |
| `alarm_count` | int | 报警计数 |

#### ProcessStep（工艺步骤）

| 字段 | 类型 | 说明 |
|------|------|------|
| `step_id` | str | 步骤唯一标识 |
| `lot_id` | str | 关联批次 |
| `eq_id` | str | 关联设备 |
| `recipe_name` | str | 配方名称 |
| `timestamp` | datetime | 执行时间 |

#### Defect（缺陷）

| 字段 | 类型 | 说明 |
|------|------|------|
| `defect_id` | str | 缺陷唯一标识 |
| `wafer_id` | str | 关联晶圆 |
| `type` | str | 缺陷类型：Particle / Scratch |
| `severity` | str | 严重程度：HIGH / MEDIUM / LOW |
| `location_x` | float | X 坐标位置 |
| `location_y` | float | Y 坐标位置 |

### Link Types（关系类型）

```
(:Lot)-[:CONTAINS]->(:Wafer)          -- 批次包含晶圆
(:Wafer)-[:PROCESSED_ON]->(:Equipment) -- 晶圆在设备上加工
(:Lot)-[:HAS_STEP]->(:ProcessStep)     -- 批次包含工艺步骤
(:ProcessStep)-[:ASSIGNED_TO]->(:Equipment) -- 步骤分配到设备
(:Wafer)-[:HAS_DEFECT]->(:Defect)     -- 晶圆存在缺陷
```

## 🔧 Agent Tools（工具集）

Agent 拥有以下工具，使用 `@tool` 装饰器定义：

### 1. query_ontology_graph

在 Ontology 知识图谱中查询节点的关联关系。

```python
@tool("query_ontology_graph")
def query_ontology_graph(node_id: str, relation: str = "", direction: str = "out") -> str
```

**参数**：
- `node_id`: 起始节点 ID，如 "Lot-W80", "ETCH-A03"
- `relation`: 关系类型过滤，可选值: CONTAINS, PROCESSED_ON, HAS_STEP, ASSIGNED_TO, HAS_DEFECT
- `direction`: 查询方向，可选值: out(出边), in(入边), both(双向)

**示例**：
```python
# 查询 Lot-W80 包含的晶圆
query_ontology_graph(node_id="Lot-W80", relation="CONTAINS", direction="out")

# 查询在 ETCH-A03 上加工过的晶圆
query_ontology_graph(node_id="ETCH-A03", relation="PROCESSED_ON", direction="in")
```

### 2. find_nodes_by_type

按类型查找所有节点。

```python
@tool("find_nodes_by_type")
def find_nodes_by_type(node_type: str) -> str
```

**参数**：
- `node_type`: 节点类型，可选值: Lot, Wafer, Equipment, ProcessStep, Defect

### 3. get_object_details

从 SQLite 中获取对象的详细属性。

```python
@tool("get_object_details")
def get_object_details(object_type: str, object_id: str) -> str
```

**参数**：
- `object_type`: 对象类型
- `object_id`: 对象 ID

### 4. hold_lot_action

Hold 住批次，防止继续加工。

```python
@tool("hold_lot_action")
def hold_lot_action(lot_id: str) -> str
```

**返回**：
```
🚨 ACTION: Holding Lot Lot-W80 - 批次已成功暂停
```

### 5. list_equipment_status

获取所有设备的状态概览。

```python
@tool("list_equipment_status")
def list_equipment_status() -> str
```

## 🚀 API 接口

### POST /investigate

启动根因分析调查。

**请求体**：
```json
{
    "query": "为什么 Lot-W80 的良率下降了？"
}
```

**响应**：
```json
{
    "final_answer": "根因分析报告...",
    "thought_chain": [
        {"type": "human", "content": "为什么 Lot-W80 的良率下降了？"},
        {"type": "ai", "content": "{\"thought\": \"我需要先查询 Lot-W80 的详细信息...\", \"action\": \"get_object_details\", ...}"},
        {"type": "tool", "content": "{\"product_name\": \"14nm-FinFET\", \"current_yield\": 0.82, ...}"},
        ...
    ],
    "tool_calls": [
        {"action": "get_object_details", "result": "{...}"},
        {"action": "query_ontology_graph", "result": "[...]"}
    ],
    "hold_lots": ["Lot-W80"]
}
```

### GET /health

健康检查。

**响应**：
```json
{"status": "healthy"}
```

### GET /graph

获取 Ontology 图结构（用于可视化）。

**响应**：
```json
{
    "nodes": [
        {"id": "Lot-W80", "node_type": "Lot", "product_name": "14nm-FinFET", "current_yield": 0.82},
        {"id": "WAFER-W80-00", "node_type": "Wafer", "slot": 0, "defect_count": 3},
        ...
    ],
    "edges": [
        {"source": "Lot-W80", "target": "WAFER-W80-00", "relation": "CONTAINS"},
        ...
    ]
}
```

## 🧪 使用示例

### 示例 1：良率下降根因分析

**用户查询**：
```
为什么 Lot-W80 的良率下降了？
```

**Agent 思考链**：
1. 查询 Lot-W80 属性 → 良率 82%（偏低，目标 >90%）
2. 查询包含晶圆 → WAFER-W80-00/-01 各有 3 个缺陷
3. 查询加工设备 → ETCH-A03（报警计数 5）、CVD-B02（报警计数 2）
4. 分析缺陷类型 → Particle（颗粒）和 Scratch（划痕）
5. 定位根因 → ETCH-A03 报警偏高，可能导致缺陷

**最终结论**：
```
根因定位：ETCH-A03 腔体报警计数为 5，明显偏高。Lot-W80 的前两片晶圆（WAFER-W80-00、WAFER-W80-01）各检测到 3 个缺陷，主要为 Particle（颗粒）类型。

建议措施：
1. 暂停 Lot-W80 继续加工
2. 检查 ETCH-A03 的腔体状态和 RF 功率稳定性
3. 排查是否存在腔体污染问题
```

### 示例 2：设备问题调查

**用户查询**：
```
ETCH-A03 设备有什么问题？
```

**Agent 行动**：
1. 获取设备详情 → alarm_count=5（偏高）
2. 查询关联晶圆 → 找到所有在该设备上加工的晶圆
3. 检查关联批次良率 → Lot-W80 良率异常
4. 建议 Hold 相关批次

### 示例 3：执行 Hold 操作

**用户查询**：
```
暂停 Lot-W80
```

**Agent 行动**：
1. 调用 hold_lot_action(lot_id="Lot-W80")
2. 返回执行结果

## 📁 项目结构

```
wafer_ontology_mvp/
├── .env                    # 环境变量配置
├── pyproject.toml          # Poetry 依赖管理
├── fab_ontology.db         # SQLite 数据库文件（自动生成）
├── README.md               # 项目文档（本文件）
├── src/                    # 后端核心代码
│   ├── main.py             # FastAPI 入口
│   ├── config.py           # 配置加载（Pydantic Settings）
│   ├── ontology/           # Ontology 核心定义
│   │   ├── __init__.py
│   │   ├── schema.py       # Object 和 Link 的 SQLModel 定义
│   │   └── graph_builder.py # OntologyBuilder（NetworkX + SQLite）
│   ├── agent/              # Agent 逻辑
│   │   ├── __init__.py
│   │   ├── state.py        # LangGraph 的 State 定义
│   │   ├── nodes.py        # Agent/Tool 节点函数
│   │   ├── tools.py        # Agent 可用工具集（@tool 装饰器）
│   │   └── graph.py        # LangGraph ReAct 循环编译
│   └── api/                # API 路由
│       ├── __init__.py
│       └── endpoints.py    # /investigate, /health, /graph
└── web/                    # Flask 前端
    ├── app.py              # Flask 后端（代理 FastAPI）
    └── templates/
        └── index.html      # 聊天界面（HTML + CSS + JS）
```

## 🔄 数据流

### 启动流程

```
[FastAPI 启动] → [lifespan 事件] → [initialize_agent()]
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ↓                     ↓                     ↓
            创建 OntologyBuilder    播种模拟数据 (seed_data)   创建 Agent 图
                    │                     │                     │
                    ↓                     ↓                     ↓
           NetworkX DiGraph      SQLite 数据库           LangGraph 编译
           (58 nodes, 111 edges)  (5 张表)              (ReAct 循环)
```

### ReAct 循环流程

```
用户查询 → GraphState.messages[] → Agent Node (LLM) → 判断 action
                                                        │
                         ┌──────────────────────────────┼──────────────────────────────┐
                         ↓ (action == "FINISH")         ↓ (action 是工具名)            ↓ (未知 action)
                 返回 final_answer              Tool Node 执行工具              返回错误信息
                 流程结束                        ↓
                                       工具结果 → GraphState.messages[]
                                       ↓
                                   回到 Agent Node
                                   继续推理循环
```

## 🧪 测试数据

系统启动时自动生成模拟数据：

| 类型 | 数量 | 说明 |
|------|------|------|
| Lot | 3 个 | Lot-W80, Lot-W81, Lot-W82 |
| Wafer | 15 片 | 每批 5 片 |
| Equipment | 4 台 | ETCH-A03, CVD-B02, LITH-C01, CMP-D01 |
| ProcessStep | 30 个 | 每片晶圆 2 个步骤 |
| Defect | 6 个 | Lot-W80 前两片各 3 个缺陷 |

**测试场景**：
- Lot-W80 良率 82%（偏低），用于 RCA 演示
- ETCH-A03 报警计数 5（偏高），作为根因候选
- LITH-C01 状态 WARNING，报警计数 8

## 📝 开发注意事项

### 环境变量加载

`.env` 文件路径使用绝对路径加载，避免工作目录影响：

```python
# src/config.py
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
```

### JSON 解析兼容性

LLM 可能返回单引号格式的 JSON，使用 `parse_llm_json()` 函数处理：

```python
# src/agent/nodes.py
def parse_llm_json(response_text: str):
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return ast.literal_eval(response_text)
```

### Windows 编码处理

在 `src/main.py` 中设置 UTF-8 编码，确保 emoji 和中文正常输出：

```python
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
```

## 🚧 扩展方向

1. **图可视化**：集成 D3.js 或 vis.js 展示知识图谱
2. **更多 Object 类型**：添加 Recipe、Alarm、RecipeParameter 等
3. **实时数据流**：接入真实 MES 系统数据
4. **向量检索**：集成 Embedding，支持语义相似度查询
5. **多 Agent 协作**：引入 Planner、Executor、Summarizer 等角色
6. **持久化改进**：使用 Redis 缓存图数据，加速查询

## 📜 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**项目状态**：✅ MVP 完成，可正常运行

**最后更新**：2026-07-19

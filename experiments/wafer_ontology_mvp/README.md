# 🔬 Wafer Fab Ontology MVP

A semiconductor wafer fab Virtual Fab Root Cause Analysis (RCA) Agent system built on **GraphRAG** and **LangGraph**. The core concept is inspired by **Palantir Ontology**: abstracting scattered data into business Objects, Links, and Actions, enabling the LLM Agent to reason at the semantic layer rather than operating directly on raw data.

## 🎯 Core Objectives

- **Semantic Abstraction**: Model wafer fab data as business entities (Lot, Wafer, Equipment, etc.)
- **Graph Reasoning**: Perform multi-hop reasoning and relationship discovery via knowledge graphs
- **Intelligent Analysis**: LLM Agent autonomously plans investigation paths to locate the root cause of quality issues
- **Actionable**: Support direct execution of business actions (e.g., holding lots)

## 🧠 Theoretical Foundation

### 1. Palantir Ontology Concepts

| Concept | Definition | Implementation in This Project |
|---------|------------|-------------------------------|
| **Object** | Business entity, e.g., lot, wafer, equipment | `Lot`, `Wafer`, `Equipment`, `ProcessStep`, `Defect` |
| **Link** | Semantic relationship between entities | `CONTAINS`, `PROCESSED_ON`, `HAS_DEFECT`, etc. |
| **Action** | Executable business operation | `hold_lot_action` |
| **Ontology Layer** | Unified semantic abstraction layer | Combined NetworkX + SQLite storage |

### 2. GraphRAG (Graph-enhanced Retrieval-Augmented Generation)

```
User Query → LLM Analysis → Graph Retrieval (Knowledge Associations) → Attribute Query (Detailed Data) → Comprehensive Reasoning → Final Conclusion
```

### 3. ReAct Loop (Reasoning + Acting)

This project uses **LangGraph** to implement the ReAct loop:

```
[Agent Node] → Think about next action → [Router] → Decide whether to call a tool
    ↑                                            ↓
    └────────────────────────────────────── [Tool Node] → Execute tool and return results
```

## 🏗️ Technical Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Interface (Flask)                       │
│                   http://localhost:5000/                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                  Chat Interface / Visualization              │    │
│  └──────────────────────────────────────┬──────────────────────┘    │
└─────────────────────────────────────────┼───────────────────────────┘
                                          │ HTTP Request
                                          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                          │
│                   http://localhost:8000/                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  /health        │  │  /investigate   │  │  /graph             │ │
│  │  Health Check   │  │  Start RCA      │  │  Export Graph       │ │
│  │                 │  │  Investigation  │  │  Structure          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent Layer (LangGraph)                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐  │    │
│  │  │ Agent    │───▶│ Router   │───▶│ Tool Execution       │  │    │
│  │  │ Node     │◀───│          │◀───│ Node                 │  │    │
│  │  │ (LLM     │    │ (Decide  │    │ (Execute             │  │    │
│  │  │ Reason-  │    │  Next    │    │  query_ontology_     │  │    │
│  │  │ ing)     │    │  Step)   │    │  graph, etc.)        │  │    │
│  │  └──────────┘    └──────────┘    └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                          │
                                          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  Ontology Layer (NetworkX + SQLite)                 │
│                                                                     │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │     NetworkX DiGraph        │  │        SQLite Database      │  │
│  │  - Store Links between     │  │  - Store Object attributes  │  │
│  │    Objects                  │  │  - Lot, Wafer, Equipment... │  │
│  │  - Support multi-hop graph │  │  - Access via SQLModel ORM  │  │
│  │    traversal queries        │  │                             │  │
│  │  - 58 nodes / 111 edges    │  │                             │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Version | Description |
|-----------|-----------|---------|-------------|
| Language | Python | 3.11+ | Core development language |
| Backend Framework | FastAPI | ^0.115.0 | RESTful API service |
| Frontend Framework | Flask | ^3.0.0 | Web interface |
| Graph Storage | NetworkX | ^3.3 | In-memory graph database (Neo4j alternative) |
| Relational Storage | SQLite + SQLModel | ^0.0.16 | Object attribute storage |
| Agent Framework | LangGraph | ^0.2.0 | ReAct loop orchestration |
| LLM Integration | LangChain | ^0.3.0 | LLM tool calling |
| LLM Model | DeepSeek | - | Accessed via OpenAI-compatible API |
| Configuration | Pydantic Settings | ^2.5.0 | Environment variable loading |

## 📦 Installation & Startup

### Prerequisites

- Python 3.11+
- `pip` or `poetry` installed

### Install Dependencies

```bash
# Navigate to the project directory
cd wafer_ontology_mvp

# Option 1: Using pip
pip install fastapi uvicorn sqlmodel networkx langchain langchain-openai langgraph python-dotenv pydantic pydantic-settings tenacity flask requests

# Option 2: Using poetry
poetry install
```

### Configure Environment Variables

Edit the `.env` file to configure the LLM API:

```env
# DeepSeek API configuration
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# FastAPI configuration (optional)
HOST=0.0.0.0
PORT=8000
```

### Start Services

**Option 1: Start separately (development/debugging)**

```bash
# Terminal 1: Start FastAPI backend
python src/main.py

# Terminal 2: Start Flask frontend
python web/app.py
```

**Option 2: Using Poetry (recommended)**

```bash
# Start backend
poetry run python src/main.py

# Start frontend (new terminal)
poetry run python web/app.py
```

### Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| FastAPI Backend | http://localhost:8000 | API endpoints |
| Flask Frontend | http://localhost:5000 | Web interface |
| API Docs | http://localhost:8000/docs | Swagger UI |

## 📊 Ontology Schema Definition

### Object Types

#### Lot

| Field | Type | Description |
|-------|------|-------------|
| `lot_id` | str | Unique lot identifier, e.g., "Lot-W80" |
| `product_name` | str | Product name, e.g., "14nm-FinFET" |
| `current_yield` | float | Current yield, between 0 and 1 |
| `status` | str | Status: RUNNING / HOLD / COMPLETED |
| `create_time` | datetime | Creation timestamp |

#### Wafer

| Field | Type | Description |
|-------|------|-------------|
| `wafer_id` | str | Unique wafer identifier |
| `slot` | int | Slot position within the lot |
| `parent_lot_id` | str | Parent lot ID |
| `defect_count` | int | Number of defects |
| `status` | str | Status |

#### Equipment

| Field | Type | Description |
|-------|------|-------------|
| `eq_id` | str | Unique equipment identifier, e.g., "ETCH-A03" |
| `type` | str | Equipment type: Etch / CVD / Lithography / CMP |
| `status` | str | Status: RUNNING / WARNING / DOWN |
| `alarm_count` | int | Alarm count |

#### ProcessStep

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | str | Unique step identifier |
| `lot_id` | str | Associated lot |
| `eq_id` | str | Associated equipment |
| `recipe_name` | str | Recipe name |
| `timestamp` | datetime | Execution timestamp |

#### Defect

| Field | Type | Description |
|-------|------|-------------|
| `defect_id` | str | Unique defect identifier |
| `wafer_id` | str | Associated wafer |
| `type` | str | Defect type: Particle / Scratch |
| `severity` | str | Severity level: HIGH / MEDIUM / LOW |
| `location_x` | float | X coordinate |
| `location_y` | float | Y coordinate |

### Link Types

```
(:Lot)-[:CONTAINS]->(:Wafer)          -- Lot contains wafers
(:Wafer)-[:PROCESSED_ON]->(:Equipment) -- Wafer processed on equipment
(:Lot)-[:HAS_STEP]->(:ProcessStep)     -- Lot has process steps
(:ProcessStep)-[:ASSIGNED_TO]->(:Equipment) -- Step assigned to equipment
(:Wafer)-[:HAS_DEFECT]->(:Defect)     -- Wafer has defects
```

## 🔧 Agent Tools

The Agent has the following tools, defined using the `@tool` decorator:

### 1. query_ontology_graph

Query node relationships in the Ontology knowledge graph.

```python
@tool("query_ontology_graph")
def query_ontology_graph(node_id: str, relation: str = "", direction: str = "out") -> str
```

**Parameters**:
- `node_id`: Starting node ID, e.g., "Lot-W80", "ETCH-A03"
- `relation`: Relationship type filter. Options: CONTAINS, PROCESSED_ON, HAS_STEP, ASSIGNED_TO, HAS_DEFECT
- `direction`: Query direction. Options: out (outgoing edges), in (incoming edges), both (bidirectional)

**Examples**:
```python
# Query wafers contained in Lot-W80
query_ontology_graph(node_id="Lot-W80", relation="CONTAINS", direction="out")

# Query wafers processed on ETCH-A03
query_ontology_graph(node_id="ETCH-A03", relation="PROCESSED_ON", direction="in")
```

### 2. find_nodes_by_type

Find all nodes by type.

```python
@tool("find_nodes_by_type")
def find_nodes_by_type(node_type: str) -> str
```

**Parameters**:
- `node_type`: Node type. Options: Lot, Wafer, Equipment, ProcessStep, Defect

### 3. get_object_details

Retrieve detailed object attributes from SQLite.

```python
@tool("get_object_details")
def get_object_details(object_type: str, object_id: str) -> str
```

**Parameters**:
- `object_type`: Object type
- `object_id`: Object ID

### 4. hold_lot_action

Hold a lot to prevent further processing.

```python
@tool("hold_lot_action")
def hold_lot_action(lot_id: str) -> str
```

**Returns**:
```
🚨 ACTION: Holding Lot Lot-W80 - Lot successfully placed on hold
```

### 5. list_equipment_status

Get an overview of all equipment statuses.

```python
@tool("list_equipment_status")
def list_equipment_status() -> str
```

## 🚀 API Endpoints

### POST /investigate

Start a root cause analysis investigation.

**Request Body**:
```json
{
    "query": "Why has the yield of Lot-W80 dropped?"
}
```

**Response**:
```json
{
    "final_answer": "Root cause analysis report...",
    "thought_chain": [
        {"type": "human", "content": "Why has the yield of Lot-W80 dropped?"},
        {"type": "ai", "content": "{\"thought\": \"I need to first query the details of Lot-W80...\", \"action\": \"get_object_details\", ...}"},
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

Health check endpoint.

**Response**:
```json
{"status": "healthy"}
```

### GET /graph

Get the Ontology graph structure (for visualization).

**Response**:
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

## 🧪 Usage Examples

### Example 1: Yield Drop Root Cause Analysis

**User Query**:
```
Why has the yield of Lot-W80 dropped?
```

**Agent Thought Chain**:
1. Query Lot-W80 attributes → Yield 82% (low, target >90%)
2. Query contained wafers → WAFER-W80-00/-01 each have 3 defects
3. Query processing equipment → ETCH-A03 (alarm count 5), CVD-B02 (alarm count 2)
4. Analyze defect types → Particle and Scratch
5. Identify root cause → ETCH-A03 has elevated alarms, likely causing defects

**Final Conclusion**:
```
Root Cause Identified: ETCH-A03 chamber alarm count is 5, significantly above normal. The first two wafers of Lot-W80 (WAFER-W80-00, WAFER-W80-01) each have 3 detected defects, predominantly of the Particle type.

Recommended Actions:
1. Place Lot-W80 on hold to stop further processing
2. Inspect ETCH-A03 chamber condition and RF power stability
3. Investigate potential chamber contamination
```

### Example 2: Equipment Issue Investigation

**User Query**:
```
What issues does equipment ETCH-A03 have?
```

**Agent Actions**:
1. Get equipment details → alarm_count=5 (elevated)
2. Query associated wafers → Find all wafers processed on this equipment
3. Check associated lot yields → Lot-W80 yield anomaly detected
4. Recommend holding affected lots

### Example 3: Execute Hold Action

**User Query**:
```
Hold Lot-W80
```

**Agent Actions**:
1. Call hold_lot_action(lot_id="Lot-W80")
2. Return execution result

## 📁 Project Structure

```
wafer_ontology_mvp/
├── .env                    # Environment variable configuration
├── pyproject.toml          # Poetry dependency management
├── fab_ontology.db         # SQLite database file (auto-generated)
├── README.md               # Project documentation (this file)
├── src/                    # Backend core code
│   ├── main.py             # FastAPI entry point
│   ├── config.py           # Configuration loading (Pydantic Settings)
│   ├── ontology/           # Ontology core definitions
│   │   ├── __init__.py
│   │   ├── schema.py       # SQLModel definitions for Objects and Links
│   │   └── graph_builder.py # OntologyBuilder (NetworkX + SQLite)
│   ├── agent/              # Agent logic
│   │   ├── __init__.py
│   │   ├── state.py        # LangGraph State definition
│   │   ├── nodes.py        # Agent/Tool node functions
│   │   ├── tools.py        # Agent toolset (@tool decorator)
│   │   └── graph.py        # LangGraph ReAct loop compilation
│   └── api/                # API routes
│       ├── __init__.py
│       └── endpoints.py    # /investigate, /health, /graph
└── web/                    # Flask frontend
    ├── app.py              # Flask backend (proxies to FastAPI)
    └── templates/
        └── index.html      # Chat interface (HTML + CSS + JS)
```

## 🔄 Data Flow

### Startup Flow

```
[FastAPI Startup] → [lifespan event] → [initialize_agent()]
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
          Create OntologyBuilder      Seed mock data (seed_data)   Create Agent graph
                    │                         │                         │
                    ↓                         ↓                         ↓
           NetworkX DiGraph          SQLite Database            LangGraph Compilation
           (58 nodes, 111 edges)     (5 tables)                 (ReAct loop)
```

### ReAct Loop Flow

```
User Query → GraphState.messages[] → Agent Node (LLM) → Determine action
                                                          │
                         ┌────────────────────────────────┼────────────────────────────────┐
                         ↓ (action == "FINISH")           ↓ (action is a tool name)        ↓ (unknown action)
                 Return final_answer              Tool Node executes tool          Return error message
                 End flow                                  ↓
                                               Tool result → GraphState.messages[]
                                               ↓
                                           Return to Agent Node
                                           Continue reasoning loop
```

## 🧪 Test Data

Mock data is automatically generated on system startup:

| Type | Count | Description |
|------|-------|-------------|
| Lot | 3 | Lot-W80, Lot-W81, Lot-W82 |
| Wafer | 15 | 5 per lot |
| Equipment | 4 | ETCH-A03, CVD-B02, LITH-C01, CMP-D01 |
| ProcessStep | 30 | 2 steps per wafer |
| Defect | 6 | 3 defects each on the first two wafers of Lot-W80 |

**Test Scenarios**:
- Lot-W80 yield at 82% (low), used for RCA demonstration
- ETCH-A03 alarm count at 5 (elevated), serving as a root cause candidate
- LITH-C01 status WARNING, alarm count 8

## 📝 Development Notes

### Environment Variable Loading

The `.env` file path is loaded using an absolute path to avoid working directory issues:

```python
# src/config.py
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
```

### JSON Parsing Compatibility

The LLM may return JSON with single quotes. Use the `parse_llm_json()` function to handle this:

```python
# src/agent/nodes.py
def parse_llm_json(response_text: str):
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return ast.literal_eval(response_text)
```

### Windows Encoding Handling

Set UTF-8 encoding in `src/main.py` to ensure proper output of emoji and non-ASCII characters:

```python
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
```

## 🚧 Future Extensions

1. **Graph Visualization**: Integrate D3.js or vis.js to display the knowledge graph
2. **More Object Types**: Add Recipe, Alarm, RecipeParameter, etc.
3. **Real-time Data Streaming**: Connect to actual MES system data
4. **Vector Search**: Integrate embeddings for semantic similarity queries
5. **Multi-Agent Collaboration**: Introduce Planner, Executor, Summarizer roles
6. **Persistence Improvements**: Use Redis to cache graph data for faster queries

## 📜 License

MIT License

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

**Project Status**: ✅ MVP complete, fully functional

**Last Updated**: 2026-07-19

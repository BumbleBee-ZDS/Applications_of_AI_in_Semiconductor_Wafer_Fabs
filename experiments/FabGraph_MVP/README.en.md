# FabGraph MVP

A wafer-fab data-asset knowledge-graph system — driven by **Schema Graph + Lineage Graph** dual graphs, powering semantic retrieval and NL2SQL.

> Design metaphor: the whole system mirrors the ResNet architecture — metadata as input features, the SQL analyzer as residual blocks injecting semantic signals layer by layer, the graphs as cross-layer connections that avoid semantic islands, and finally NL2SQL as the output head producing SQL.

## Features

- **Metadata management**: tables / fields / stored procedures / SQL history, persisted in SQLite
- **Schema Graph**: table - field - FK - inferred JOIN relationship graph
- **Lineage Graph**: data-lineage hypergraph formed by procedures reading/writing tables
- **Semantic retrieval**: vector nearest-neighbor + 1-hop graph expansion recall
- **NL2SQL**: retrieval-augmented + JOIN-path constrained + LLM-generated Oracle SQL
- **Graph algorithms**: JOIN shortest path, community detection (Louvain / Girvan-Newman)
- **Mock fallback**: automatically degrades without LLM API keys / embedding models; runs out of the box

## Architecture Layers

```
api        -> FastAPI routing layer (request validation + service calls + structured JSON)
service    -> business orchestration layer (semantic retrieval / NL2SQL / graph construction / SQL analysis)
repository -> data-access layer (SQLite metadata / pickle graphs / FAISS vectors)
graph      -> graph construction and algorithms (NetworkX)
models     -> Pydantic data models
utils      -> LLM client / embedding client / SQL parser / exception hierarchy
```

Dependency direction: `api -> service -> repository / graph -> models / utils`; reverse dependencies are forbidden.

## Directory Structure

```
FabGraph_MVP/
├── configs/settings.yaml      # Configuration (${VAR:default} placeholders expanded by .env)
├── data/
│   ├── mock_oracle/           # Simulated fab metadata JSON
│   ├── fabgraph.db            # SQLite metadata database (generated at runtime)
│   ├── schema_graph.pkl       # Schema Graph snapshot
│   ├── lineage_graph.pkl      # Lineage Graph snapshot
│   └── faiss_index/           # FAISS vector index
├── scripts/init_mock_data.py  # Generates simulated metadata
├── src/fabgraph/
│   ├── main.py                # FastAPI startup entry
│   ├── config.py              # YAML + .env configuration loading
│   ├── api/                   # FastAPI app + routes + dependency injection
│   ├── service/               # Business orchestration services
│   ├── repository/            # Metadata / graph / vector repositories
│   ├── graph/                 # Graph construction and algorithms
│   ├── models/                # schema / graph / semantic models
│   └── utils/                 # LLM / embedding / SQL parsing / exceptions
├── ui/streamlit_app/
│   ├── app.py                 # Streamlit entry
│   ├── services.py            # Cached service instances
│   ├── graph_viz.py           # pyvis visualization components
│   ├── page_metadata.py       # Metadata browsing
│   ├── page_graph.py          # Graph visualization
│   ├── page_search.py         # Semantic search
│   ├── page_nl2sql.py         # NL2SQL
│   └── page_sql_analyzer.py   # SQL analysis
├── tests/                     # pytest test suite
├── Dockerfile / docker-compose.yml
└── pyproject.toml
```

## Quick Start

### Requirements

- Python >= 3.11
- A venv / conda isolated environment is recommended

### Installation

```bash
# Enter the project root after cloning
pip install -e ".[dev]"
```

### Configuration

Edit `.env` (refer to `.env.example`):

```dotenv
# LLM: leave empty to enable mock mode automatically
DEEPSEEK_API_KEY=sk-xxx
USE_MOCK_LLM=false          # false=real LLM, true=Mock fallback
USE_MOCK_EMBEDDINGS=true    # keep true without sentence-transformers
```

All `${VAR:default}` placeholders in `configs/settings.yaml` preferentially read environment variables and fall back to defaults when missing — no editing required to run.

### Generate Simulated Data

```bash
python scripts/init_mock_data.py
```

Produces `data/mock_oracle/{tables,columns,procedures,sql_history}.json`, containing 8 core tables, mixed-naming-style fields, procedure lineage, and 50+ historical SQL statements.

### Launch the API Service

```bash
# Option 1: start directly with uvicorn
uvicorn fabgraph.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: module entry
python -m fabgraph.main
```

After startup, visit:
- API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

### Launch the Streamlit UI

```bash
streamlit run ui/streamlit_app/app.py
```

Visit <http://localhost:8501> and switch in the sidebar:
- Metadata browsing
- Graph visualization (Schema / JOIN / Lineage / community detection)
- Semantic search
- NL2SQL
- SQL analysis

### Docker Deployment

```bash
docker-compose up --build
```

Starts both the API (8000) and the UI (8501).

## API Overview

| Method | Path | Description |
|------|------|------|
| GET  | `/health` | Health check |
| GET  | `/api/metadata/tables` | Table list |
| GET  | `/api/metadata/tables/{name}` | Table details (with fields) |
| GET  | `/api/metadata/procedures` | Stored-procedure list |
| GET  | `/api/metadata/sql-history` | Historical SQL |
| POST | `/api/metadata/reload` | Reload metadata |
| GET  | `/api/graph/schema/summary` | Schema Graph summary |
| GET  | `/api/graph/schema/nodes` | Schema Graph nodes |
| GET  | `/api/graph/schema/edges` | Schema Graph edges |
| GET  | `/api/graph/lineage/summary` | Lineage Graph summary |
| GET  | `/api/graph/lineage/hyperedges` | Lineage hyperedge list |
| GET  | `/api/graph/lineage/upstream/{table}` | Upstream tables |
| GET  | `/api/graph/lineage/downstream/{table}` | Downstream tables |
| GET  | `/api/graph/communities` | Community detection |
| GET  | `/api/graph/join-path` | JOIN path lookup |
| POST | `/api/search/search` | Semantic search |
| POST | `/api/search/search-tables` | Table-level search only |
| POST | `/api/search/reindex` | Rebuild vector index |
| POST | `/api/nl2sql/generate` | Generate SQL |
| POST | `/api/nl2sql/analyze` | Analyze a single SQL statement |
| POST | `/api/nl2sql/analyze-batch` | Batch-analyze SQL |

All `FabGraphError` subclass exceptions return structured JSON; HTTP status codes map by exception type (404 / 422 / 500 / 502).

## Testing

```bash
pytest                          # full suite
pytest tests/test_graph_algorithms.py  # single module
pytest --cov=fabgraph           # coverage
```

Tests use the `tmp_path` fixture to isolate database and graph files, without polluting the repository. LLM and embedding clients both go through Mock paths in tests.

## Key Design

### Dual Graphs

- **Schema Graph** (`MultiDiGraph`): table -> field (`has_column`), field <-> field (`foreign_key` / `join_inferred`). Projected to a table-level undirected JOIN graph for shortest-path algorithms.
- **Lineage Graph** (`MultiDiGraph`): procedures reading/writing tables (`reads` / `writes`); procedures act as hyperedges connecting input/output table sets; table -> table `lineage` edges are also derived.

### Retrieval Augmentation

`SemanticSearchService` first recalls via vector nearest-neighbors, then performs 1-hop expansion using the Schema Graph (fields of a hit table get a 0.7x score boost), avoiding pure vector-similarity misses of remotely related semantic fields.

### NL2SQL Orchestration

1. Semantic search recalls relevant tables
2. `JoinPathFinder` computes multi-table connected paths on the JOIN graph
3. Assemble Schema context (DDL + JOIN conditions)
4. LLM generates Oracle SQL
5. `SqlParser` validates syntactic correctness

### ResNet Metaphor

| ResNet concept | FabGraph counterpart |
|-------------|---------------|
| Input features | Raw metadata (tables/fields/procedures) |
| Residual blocks | SQL analyzer, injecting semantic signals per SQL statement |
| Cross-layer connections | Graphs propagate inter-table semantics and lineage |
| Global pooling | Dependency-injected shared singletons |
| Output head | NL2SQL / retrieval results |
| Attention | JOIN path weights / community clustering |

## Configuration Reference

Full configuration is in `configs/settings.yaml`; key items:

| Config | Default | Description |
|------|--------|------|
| `llm.use_mock` | true | Uses preset responses without an API key |
| `llm.provider` | deepseek | openai / deepseek |
| `embedding.use_mock` | true | Falls back to TF-IDF without a model |
| `embedding.dimension` | 384 | Embedding dimension (must match the model) |
| `nl2sql.max_join_hops` | 3 | Maximum JOIN path hops |
| `search.hop_expansion` | 1 | Graph expansion hops |
| `app.port` | 8000 | API port |

## License

MIT

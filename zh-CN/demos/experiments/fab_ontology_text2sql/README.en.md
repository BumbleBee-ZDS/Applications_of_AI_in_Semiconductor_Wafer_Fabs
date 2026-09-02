# 🏭 Fab Ontology Text2SQL (Semiconductor Fab MVP)

A minimal runnable project for FAB Text2SQL based on the **Palantir Ontology three-layer architecture**.
It abandons the fragile "natural language directly translated to SQL" pattern, and instead adopts a three-stage architecture of **semantic layer for concept mapping, kinetic layer for templated queries, and dynamic layer for data execution** — the LLM is only responsible for intent recognition and parameter extraction, and **never freely writes JOIN / WHERE**.

## 1. Architecture Overview (Palantir Ontology Mapping)

```
User natural language "help me check the yield trend of Tool 3 last week"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ ① Semantic Layer (ontology_dict.json + Schema Parser)        │
│    business jargon → fields: Tool 3→EQP-003; yield→YIELD_RATE│
│    last week→last 7 days; film abnormal→FILM_THICKNESS∉[4500,5000]
│    ✂ Schema Parser: inject only matched snippets to the LLM, │
│      saving tokens                                           │
├─────────────────────────────────────────────────────────────┤
│ ② Kinetic Layer (FabQueryAgent)                              │
│    LLM outputs a structured JSON plan (object/metric/trend/  │
│    equipment/time); falls back to a local rule engine offline│
├─────────────────────────────────────────────────────────────┤
│ ③ Kinetic Template Library (sql_templates/*.sql)             │
│    12 predefined query templates, parameter whitelist check  │
│    + parameterized binding (injection-safe)                  │
├─────────────────────────────────────────────────────────────┤
│ ④ Dynamic Layer (mock_db.py → data/fab.db)                   │
│    4 core tables: EQUIPMENT / LOT_INFO /                     │
│                  WAFER_METROLOGY / PROCESS_LOG               │
└─────────────────────────────────────────────────────────────┘
```

| Layer | File | Responsibility |
|---|---|---|
| Semantic layer | `ontology_dict.json`, `ontology.py::OntologyDictionary` | Business concept ↔ field mapping, Schema Parser (filters injected snippets by question) |
| Kinetic layer | `ontology.py::FabQueryAgent`, `sql_templates/*.sql` | Intent extraction (LLM/rules) → template selection → parameterized SQL |
| Dynamic layer | `mock_db.py` | SQLite table creation + Mock data (generated relative to "today", so "last week" is always queryable) |
| Presentation shell | `app.py` | Streamlit chat UI + "thought-chain Trace" panel |

## 2. Directory Structure

```
fab_ontology_text2sql/
├── app.py                    # Streamlit main program (UI + Trace panel)
├── ontology.py               # Semantic layer (OntologyDictionary) + Kinetic layer (FabQueryAgent)
├── mock_db.py                # Dynamic layer: SQLite tables + Mock data generation
├── ontology_dict.json        # Semantic layer: fab ontology dictionary (business jargon ↔ fields)
├── sql_templates/            # Kinetic layer: predefined query template library
│   ├── get_yield_trend.sql            Yield trend (by day)
│   ├── get_equipment_yield.sql        Average yield / equipment ranking
│   ├── get_film_stats.sql             Film thickness statistics
│   ├── get_film_thickness_trend.sql   Film thickness trend
│   ├── get_film_abnormal.sql          List of wafers with abnormal film thickness
│   ├── get_defect_stats.sql           Defect statistics
│   ├── get_defect_high.sql            List of wafers with high defects
│   ├── get_lot_status.sql             Lot details
│   ├── get_lot_list.sql               Lot list
│   ├── get_process_log_by_lot.sql     Process log by lot
│   ├── get_process_log_by_equipment.sql  Process log by equipment
│   └── get_equipment_status.sql       Equipment status
├── requirements.txt          # Dependencies
├── .env                      # DeepSeek / DashScope API config (already present)
└── data/fab.db               # SQLite database auto-generated at runtime
```

## 3. Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch (configure DeepSeek API in .env; falls back to the offline rule engine automatically if not set)
streamlit run app.py
```

> The sidebar lets you toggle the LLM in real time and change the model / Base URL / API Key (OpenAI SDK compatible format — you can swap in any local vLLM / Ollama / cloud service).

## 4. Example Questions

| Natural language | Semantic-layer hits | Kinetic-layer template |
|---|---|---|
| Help me check the yield trend of Tool 3 last week | alias Tool 3, metric yield, time last week | get_yield_trend.sql |
| Which wafers have abnormal film thickness? | metric film, condition film abnormal | get_film_abnormal.sql |
| Average yield ranking by equipment | metric yield | get_equipment_yield.sql |
| Process log of LOT-2026-001 | object process, lot number | get_process_log_by_lot.sql |
| Which wafers have high defects | metric defect, condition high defect | get_defect_high.sql |
| Current status of all equipment | object equipment | get_equipment_status.sql |

## 5. Design Points

1. **The LLM never writes SQL**: the LLM only outputs structured JSON (object/metric/trend/equipment/…); any illegal value is filtered to empty by the `_validate_plan` whitelist.
2. **All SQL is predefined**: 12 `sql_templates/*.sql` files; the Agent selects a template by the plan and fills in `?` placeholders; optional equipment filtering uses `EQP_ID = COALESCE(?, EQP_ID)`, with no string concatenation ever.
3. **Token savings**: the Schema Parser injects only ontology snippets relevant to the question into the LLM (see "injected N / total M" in the chat).
4. **Offline-capable**: falls back to the local rule engine automatically when no API key is configured or a call fails.
5. **Mock data mirrors the business**: ~4% of wafers have abnormal film thickness, a few have high defects, and yield is negatively correlated with defects.

## 6. Extension Directions

- Add a permission layer (filter customer/product fields by user/department)
- Replace the rule engine with Few-shot prompts or a fine-tuned small model
- Result caching + a glossary to support alias expansion
- Connect real MES/APC data sources to replace mock_db

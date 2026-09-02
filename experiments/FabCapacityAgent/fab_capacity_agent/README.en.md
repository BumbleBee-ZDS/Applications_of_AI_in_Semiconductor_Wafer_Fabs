# 🏭 FabCapacityAgent — Fab AI Capacity Intelligence Hub

> Semiconductor Fab Capacity Intelligence Agent
>
> A lightweight Agent framework based on the PTA (Perceive-Think-Act) loop, enabling **real-time monitoring, historical analysis, and predictive planning** of semiconductor fab capacity.

---

## 📌 Project Intro

FabCapacityAgent is an AI capacity-computing MVP system for semiconductor fabs. Through 4 chained Agents (Perception → Analysis → Decision → Execution), it automatically completes fab-wide capacity data collection, bottleneck diagnosis, prediction simulation, and report generation, helping capacity engineers quickly locate bottlenecks and evaluate optimization plans.

### ✨ Core Features

| Feature | Description |
|------|------|
| 🧠 **Self-built PTA Agent framework** | No LangChain/AutoGen dependency; a lightweight Perceive-Think-Act loop |
| 🤖 **LLM enhancement (optional)** | Supports DeepSeek / Qwen; automatically falls back to local templates when unconfigured |
| 📊 **Streamlit multi-page app** | Deep-blue tech style, 6 pages, Chinese UI |
| 🗄 **SQLite + simulated MES data** | 90-day history / 120 tools / 50–80k process records, auto-generated on first run |
| 📈 **Plotly interactive charts** | OEE / WIP / trends / heatmaps / Pareto / Monte Carlo |
| 🎯 **What-If simulation** | Add tools / adjust OEE / PM optimization / new products / combined scenarios + risk assessment |

---

## 🚀 Quick Start

### 1. Requirements

- Python 3.11+
- Windows / macOS / Linux
- (optional) DeepSeek or Qwen API key

### 2. Install Dependencies

```bash
cd fab_capacity_agent
pip install -r requirements.txt
```

### 3. (Optional) Configure LLM API Keys

Create a `.env` file in the project root (FabCapacityAgent/.env):

```ini
# DeepSeek API (https://platform.deepseek.com/)
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Aliyun Qwen / DashScope (https://dashscope.console.aliyun.com/)
DASHSCOPE_API_KEY=sk-your-qwen-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

> **When unconfigured**: the system automatically falls back to local statistical models/templates; functionality is unaffected.

### 4. Launch the App

```bash
streamlit run app.py
```

On first launch it automatically:
1. Creates the SQLite database (`data/fab_capacity.db`)
2. Generates 90 days of simulated MES data (~30–60 seconds)
3. Opens http://localhost:8501 in the browser

---

## 📐 System Architecture

```
User query / scheduled trigger
         ↓
┌──────────────────────────────────────────────┐
│           Orchestrator                       │
│                                              │
│   ┌────────────┐    ┌────────────┐           │
│   │ Perception │───▶│ Analysis   │           │
│   │   Agent    │    │   Agent    │           │
│   │  collect   │    │  analyze   │           │
│   │  data      │    │  bottleneck│           │
│   └────────────┘    └────────────┘           │
│         ↓                  ↓                 │
│   ┌────────────┐    ┌────────────┐           │
│   │ Decision   │───▶│ Execution  │           │
│   │   Agent    │    │   Agent    │           │
│   │  generate  │    │  output    │           │
│   │  decision  │    │  report    │           │
│   └────────────┘    └────────────┘           │
└──────────────────────────────────────────────┘
         ↓
  capacity analysis report + optimization advice + What-If comparison
```

### PTA Loop

Each Agent follows the **Perceive-Think-Act** three stages:

| Stage | Description |
|------|------|
| **Perceive** | Collect data from the database / upstream Agent output |
| **Think** | Call computing services / LLM for analysis and decisions |
| **Act** | Output structured results, write them back to the context for downstream consumption |

---

## 📁 Project Structure

```
fab_capacity_agent/
├── app.py                          # Streamlit main entry (home dashboard)
├── requirements.txt                # Python dependencies
│
├── config/
│   └── settings.yaml               # Global config (DB/line/Agent/UI)
│
├── data/
│   ├── generator.py                # MES simulated-data generator
│   ├── fab_capacity.db             # SQLite database (auto-generated)
│   └── reports/                    # Agent-generated reports (auto-generated)
│
├── models/
│   ├── database.py                 # DB manager (connection/DDL/CRUD)
│   ├── equipment.py                # Equipment & event models + DAO
│   ├── wafer.py                    # Lot & process models + DAO
│   └── capacity.py                 # Capacity snapshot + daily output DAO + Agent log DAO
│
├── services/
│   ├── capacity_calculator.py      # OEE/UPH/WIP/Snapshot computation
│   ├── predictor.py                # Capacity prediction (MA + LR + LLM)
│   ├── bottleneck_detector.py      # Bottleneck detection + root-cause analysis + recommendations
│   └── what_if_simulator.py        # What-If simulation + Monte Carlo
│
├── agents/
│   ├── base_agent.py               # PTA base class (perceive/think/act/run)
│   ├── perception_agent.py         # Perception Agent: collect data, build snapshot
│   ├── analysis_agent.py           # Analysis Agent: trends/bottlenecks/anomalies
│   ├── decision_agent.py           # Decision Agent: prediction + What-If
│   ├── execution_agent.py          # Execution Agent: generate report
│   └── orchestrator.py             # Orchestrator: chains the 4 Agents
│
├── pages/                          # 5 Streamlit sub-pages
│   ├── 1_📊_Realtime.py            # Equipment status/WIP/Move real-time dashboard
│   ├── 2_📈_History.py             # Trends/anomalies/bottleneck diagnosis/Pareto
│   ├── 3_🎯_Planning.py            # Prediction/What-If/Monte Carlo
│   ├── 4_🤖_AgentWorkbench.py      # Full-pipeline run/single-Agent debug/reports
│   └── 5_⚙️_Settings.py            # LLM config/database management/about
│
├── tests/
│   └── test_capacity.py            # Unit tests (23 cases)
│
└── utils/
    ├── constants.py                # Global constants (processes/statuses/KPIs/colors)
    ├── helpers.py                  # General utilities (config/log/format/decorators)
    ├── llm_client.py               # LLM client (DeepSeek/Qwen)
    └── ui_components.py            # Streamlit shared UI components
```

---

## 📊 Business Coverage

### 8 Main Process Steps

| Code | Name | Tool type | Standard time (h) |
|------|--------|----------|-------------|
| WET | Clean | Wet_Bench | 1.0 |
| PHOTO | Lithography | Scanner | 2.5 |
| ETCH | Etch | Etcher | 1.8 |
| DEPO | Deposition | Deposition | 3.2 |
| IMP | Ion Implant | Implanter | 1.2 |
| DIFF | Diffusion | Furnace | 6.0 |
| CMP | Polish | CMP_Tool | 1.5 |
| METRO | Metrology | Metrology | 0.8 |

### 3 Products

| Product | Name | Priority | Layers | Baseline yield |
|------|--------|--------|------|---------|
| Logic_A | Logic chip A | 1 | 12 | 92% |
| Logic_B | Logic chip B | 2 | 10 | 94% |
| Memory_C | Memory chip C | 3 | 8 | 96% |

### Core KPIs

| KPI | Description | Formula |
|-----|------|------|
| **OEE** | Overall equipment effectiveness | Availability × Performance × Quality |
| **UPH** | Units per hour | completed wafers / run hours |
| **WIP** | Work-in-process | current unfinished lot wafers |
| **CycleTime** | Cycle time | end_time - start_time |
| **Throughput** | Throughput | completed wafers in the period |
| **BottleneckRate** | Bottleneck rate | bottleneck step utilization / fab average |

### Database Tables (6)

| Table | Description | Expected rows |
|------|------|---------|
| equipment | Equipment master data | 120 |
| lots | Lot information | ~5,000 |
| lot_history | Process history | ~70,000 |
| equipment_events | Equipment events | ~10,000 |
| daily_output | Daily output summary | ~90 |
| agent_logs | Agent execution logs | grows continuously |

---

## 🎯 Agent Details

### 1. PerceptionAgent

- **Responsibility**: collect the last N hours of data from the database and build a `CapacitySnapshot`
- **Input**: `window_hours` (default 24h)
- **Output**: fab/step-level KPI snapshot (OEE/WIP/UPH/utilization/bottleneck ranking)
- **Service called**: `CapacityCalculator.build_snapshot()`

### 2. AnalysisAgent

- **Responsibility**: trend analysis + anomaly detection + bottleneck diagnosis
- **Input**: Perception's snapshot + the last N days of history
- **Output**: bottleneck report (bottleneck step / root cause / optimization recommendations)
- **Service called**: `BottleneckDetector.detect_and_report()`
- **LLM enhancement**: generates a natural-language trend summary

### 3. DecisionAgent

- **Responsibility**: capacity prediction + What-If scenario simulation
- **Input**: Analysis's bottleneck report
- **Output**: 7/30-day forecasts + 8 What-If scenario comparisons
- **Services called**: `Predictor.forecast_output()` + `WhatIfSimulator.compare_scenarios()`

### 4. ExecutionAgent

- **Responsibility**: summarizes the previous three steps' results into a Markdown capacity analysis report
- **Input**: snapshot + analysis report + decision plan
- **Output**: structured report (executive summary/KPIs/bottlenecks/What-If/recommendations)
- **LLM enhancement**: report polish
- **Persistence**: reports auto-saved to `data/reports/`

---

## 🧪 Testing

```bash
# Option 1: run directly (recommended, no external dependencies)
python tests/test_capacity.py

# Option 2: pytest (requires resolving the pytest_flask plugin conflict)
python -m pytest tests/test_capacity.py -v -p no:flask
```

Test coverage (23 cases):

| Test class | Cases | Coverage |
|--------|--------|---------|
| TestDatabase | 5 | Connection/table structure/row counts |
| TestCapacityCalculator | 5 | OEE/WIP/Snapshot/theoretical capacity/JSON serialization |
| TestPredictor | 2 | Single-target/multi-target prediction |
| TestBottleneckDetector | 1 | Bottleneck-detection report |
| TestWhatIfSimulator | 4 | Baseline/preset/comparison/custom scenarios |
| TestAgents | 2 | PerceptionAgent standalone/Orchestrator single Agent |
| TestOrchestratorPipeline | 1 | Full pipeline (4 chained Agents) |
| TestUtils | 3 | safe_div/safe_round/constants |

---

## ⚙️ Configuration

Key config items in `config/settings.yaml`:

```yaml
# Database
database:
  path: "data/fab_capacity.db"
  auto_init: true                  # auto-create DB on first run

# Data generator
data_generator:
  history_days: 90                 # historical data days
  lots_per_day: 60                 # daily lots started
  seed: 42                         # random seed (reproducible)

# Agent
agent:
  orchestrator:
    timeout: 300                   # full-pipeline timeout (seconds)
    max_retries: 2                 # failure retry count

# What-If simulation
simulator:
  monte_carlo_iterations: 100      # Monte Carlo iterations
```

---

## 🔧 FAQ

### Q1: Is first launch slow?

The first run generates 90 days of simulated data (~30–60 seconds); later launches skip this. To rebuild data, go to "Settings → Database management → Rebuild data".

### Q2: Should LLM enhancement be enabled?

- **Disabled**: local statistical models already satisfy basic prediction/analysis needs
- **Enabled**: more natural reports, smarter trend summaries, more specific bottleneck recommendations
- Toggle "Enable LLM enhancement" in the Agent Workbench

### Q3: How do I adjust the simulated-data scale?

Modify `config/settings.yaml`:
```yaml
data_generator:
  history_days: 30       # change to 30 days
  lots_per_day: 30       # change to 30 lots/day
```
Then force-regenerate via "Settings → Rebuild data".

### Q4: Streamlit page blank?

1. Check the terminal for Python errors
2. Confirm the database is initialized: `python models/database.py`
3. Clear the browser cache and refresh

### Q5: pytest reports a pytest_flask error?

This is an incompatibility between the pytest_flask plugin and newer Flask, unrelated to this project. Solutions:
```bash
# Option 1: disable the flask plugin
python -m pytest tests/test_capacity.py -v -p no:flask

# Option 2: run directly (recommended)
python tests/test_capacity.py
```

---

## 🛠 Tech Stack

| Module | Technology | Version requirement |
|------|------|---------|
| UI framework | Streamlit | ≥ 1.28 |
| Data processing | pandas + numpy | ≥ 2.0 / ≥ 1.24 |
| Machine learning | scikit-learn | ≥ 1.3 |
| Charts | Plotly | ≥ 5.17 |
| Storage | SQLite (built-in) | - |
| Config management | PyYAML + python-dotenv | ≥ 6.0 / ≥ 1.0 |
| LLM client | requests (OpenAI-compatible API) | ≥ 2.31 |
| Agent framework | Self-built PTA (no external dependency) | - |

---

## 📜 License

MIT License - for learning and research purposes only.

---

## 🤝 Contributing

Issues and PRs to improve the system are welcome!

---

*FabCapacityAgent v1.0 · Powered by Streamlit + SQLite + Plotly + PTA Agent Framework*

# 🏭 fab_rtd_llm_agent_mvp

An MVP project that simulates a semiconductor **12-inch fab RTD (Real-Time Dispatching) system** enhanced by LLM Agents.
Built on **Python + Streamlit multi-page**, making real calls to **DeepSeek (reasoning) + Aliyun Qwen (vectorization)** LLM APIs.

## ✨ Feature Overview

- 📡 **Real-time monitoring**: simulates 8 tools / 8 lots / PM schedule / zone bottleneck load, with one-click injection of 4 process anomalies
- 🔍 **Full Agent pipeline**: Perception (threshold) → Diagnosis (Qwen RAG + DeepSeek v4-pro) → Scheduling (DeepSeek v4-pro) → RL simulation evaluation
- ✅ **Human approval**: L1~L4 risk grading; L3 needs 2 approvers, L4 needs 3; low-risk actions execute automatically
- 📜 **Audit log**: full-pipeline trace_id tracking with JSON export
- 📚 **Knowledge base**: 10 process knowledge documents (CVD / litho / etch / Q-Time / PM, etc.), Qwen Embedding + cosine-similarity RAG retrieval

## 🧩 Agent Architecture

```
Perception Agent(threshold) → Diagnosis Agent(Qwen RAG + DeepSeek v4-pro) → Scheduling Agent(DeepSeek v4-pro)
     → RL Simulation(heuristic reward + perturbation exploration) → Execution Agent(L1~L4 grading + approval) → Audit Agent(full-pipeline logs)
```

| Stage | Model | Description |
|---|---|---|
| Diagnosis | `deepseek-v4-pro` + `qwen3.7-text-embedding` | RAG retrieves Top-3 knowledge → root cause / quality impact / scheduling advice |
| Scheduling | `deepseek-v4-pro` | Generates dispatch policy under Q-Time / Recipe compatibility / PM / HOLD constraints |
| Vectorization | `qwen3.7-text-embedding` | dimensions=1024, text_type distinguishes query/document |

## 🚀 Quick Start

### 1. Configure API Keys

```bash
cp .env.example .env
# Edit .env and fill in real keys:
#   DEEPSEEK_API_KEY=sk-xxx
#   DASHSCOPE_API_KEY=sk-xxx
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch

```bash
streamlit run app.py
```

On first launch, the Qwen API is automatically called to vectorize the knowledge base (10 documents, ~1–2 API calls).

### 4. Walkthrough

1. **1 Real-time monitoring**: select an anomaly scenario from the dropdown (temperature drift / pressure anomaly / EPD loss / Overlay out of tolerance) → click "Refresh / Inject"
2. **2 Agent analysis**: click "Run full pipeline" to view the perception event, diagnosis report (with confidence progress bars and knowledge-base citations), dispatch policy, and RL ranking
3. **3 Human approval**: L1/L2 auto-execute; L3/L4 generate approval tickets, executed after multi-person approval
4. **4 Audit log**: trace by trace_id across the full pipeline, export JSON
5. **5 Knowledge base**: arbitrary RAG retrieval demo

## 🌡 Injectable Anomaly Scenarios

| Scenario | Injection Location | Perception Threshold |
|---|---|---|
| CVD temperature drift | CVD-001 temperature +1.2°C | Deviation from recipe center ≥0.5°C |
| CVD pressure anomaly | CVD-003 pressure +22% | Deviation from recipe center ≥15% |
| Etch EPD loss | ETCH-201 EPD signal 0.05 | EPD < 0.3 |
| Litho Overlay out of tolerance | LITHO-101 Overlay 9.2nm | Exceeds spec by 3.0nm |

## 🛡 Graceful Degradation Without Keys

When `DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY` are not configured:
- The Diagnosis Agent falls back to **rule-based diagnosis** (with the degradation reason noted);
- The Scheduling Agent falls back to **heuristic greedy dispatch**;
- Knowledge-base vectorization falls back to **local hash pseudo-vectors** (the RAG flow remains demonstrable);
- RL simulation, approval, and audit are fully unaffected.

## 📁 Directory Structure

```
fab_rtd_llm_agent_mvp/
├── .env.example            # Environment variable template
├── requirements.txt
├── app.py                  # Streamlit main page + sidebar
├── data/
│   └── factory_simulator.py # Factory real-time data simulator (anomaly injection)
├── agents/
│   ├── perception_agent.py  # Perception: anomaly detection
│   ├── diagnosis_agent.py   # Diagnosis: RAG + DeepSeek root-cause analysis
│   ├── scheduling_agent.py  # Scheduling: DeepSeek dispatch policy
│   ├── execution_agent.py   # Execution: risk grading + approval
│   ├── rl_simulator.py      # RL simulation evaluation
│   └── audit_agent.py       # Audit: full-pipeline logs
├── utils/
│   ├── llm_client.py        # DeepSeek + Qwen client wrapper
│   ├── knowledge_base.py    # Process knowledge base + RAG retrieval
│   └── helpers.py           # General utilities, session init
└── pages/                   # Streamlit multi-page
    ├── 1_RealTimeMonitor.py
    ├── 2_AgentAnalysis.py
    ├── 3_HumanApproval.py
    ├── 4_AuditLog.py
    └── 5_KnowledgeBase.py
```

## ⚙️ Tech Stack

Python 3.10+ · Streamlit ≥1.38 · pandas · numpy · scikit-learn · plotly · openai ≥1.40 · python-dotenv

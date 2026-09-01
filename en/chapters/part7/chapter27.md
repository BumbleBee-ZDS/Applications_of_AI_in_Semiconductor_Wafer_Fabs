# Chapter 27 Hands-On Lab — Running the Key Concepts

## 27.1 Why Hands-On Experiments Matter

The first 26 chapters follow a thread of concepts, architectures, and industry case studies, complemented by demo scripts (`matplotlib` visualizations under `zh-CN/demos/`) designed for quick visual understanding. But turning knowledge into engineering capability requires a second layer: **complete systems you can run locally** — with real code structure, interactive interfaces, and tunable parameters.

This chapter presents 9 hands-on experiments, all drawn from MVP projects the author has built and validated in real development work, organized by topic and mapped to the corresponding main-text chapters:

| Experiment | Topic | Related Chapters / Difficulty | Difficulty |
| --- | --- | --- | --- |
| 27.3 Ontology-Driven Text2SQL | Ontology semantic layer + controlled SQL generation | Ch. 24/25, Ch. 17 | ★☆☆ |
| 27.4 Wafer Fab Ontology MVP (RCA Agent) | Ontology graph + GraphRAG + ReAct | Ch. 24/25, Ch. 2/14 | ★★☆ |
| 27.5 FabGraph Dual-Graph Knowledge Platform | Schema/Lineage graphs + NL2SQL | Ch. 14/13/17 | ★★★ |
| 27.6 K8s-Style Declarative Scheduling | Control-theoretic loop + multi-Agent scheduling | Ch. 7/20 | ★☆☆ |
| 27.7 Capacity Planning PTA Agent | Perceive-Think-Act + What-If simulation | Ch. 10 | ★★☆ |
| 27.8 LoRA Fine-Tuning: Two-Stage Query Enhancement | Data synthesis + fine-tuning + evaluation | Ch. 15/17 | ★★★ |
| 27.9 RTD Real-Time Dispatching & Human-AI Collaboration | Tiered approval + audit trail | Ch. 8/11/22 | ★★☆ |
| 27.10 CIM Trusted System Red-Blue Adversarial Exercise | Rule + embedding + LLM hybrid verification | Ch. 22/23 | ★★☆ |
| 27.11 Multi-Agent Evaluation Framework | Evaluating quality / cost / resilience | Ch. 2/21 | ★☆☆ |

> All experiment code lives in the repository under `zh-CN/demos/experiments/` (each project includes its own README). Except where noted as requiring an API key, all experiments run offline; those that use an LLM provide a mock/fallback mode so you can experience the core workflow without a key.

## 27.2 Lab Environment Setup

- **Python**: 3.10+ (FabGraph and the fine-tuning experiment recommend 3.11+)
- **Common dependencies**: `pip install -r requirements.txt` (inside each project directory)
- **API Key (optional)**: some experiments call large models such as DeepSeek or Qwen; set `API_KEY` in the `.env` file to enable a real LLM. When no key is configured, the system automatically falls back to a rule engine or mock mode.
- **GPU (recommended only for the fine-tuning experiment)**: the LoRA training in 27.8 runs on CPU (albeit slowly); an NVIDIA GPU significantly accelerates it.

Each experiment section follows a three-part format — "What you'll learn / How to run / What to observe." We recommend running the experiment end-to-end first, then tweaking parameters, and finally modifying a piece of logic to observe how the system behavior changes — this is the fastest path to understanding the architectural design intent.

## 27.3 Experiment 1: Ontology-Driven Text2SQL (fab_ontology_text2sql)

**Related Chapters**: Ch. 24 (Palantir & Ontology), Ch. 25 (Ontology Construction), Ch. 17 (Fusion Overview)

**What you'll learn**: This is the shortest path to understanding "why LLMs should not freely generate SQL." The experiment implements a three-layer Text2SQL pipeline inspired by Palantir's Ontology philosophy:

- **Semantic layer**: an ontology dictionary defines the fab's concepts, entities, and relationships (Lot, Wafer, Equipment, Defect, …)
- **Power layer**: 12 predefined SQL templates — the LLM is responsible only for "selecting a template + filling in parameters," never generating free-form SQL
- **Dynamic layer**: a SQLite execution engine returns results and renders charts

This architecture ensures **controllable, auditable, and explainable results** — a direct engineering embodiment of "Ontology as a controlled semantic layer" emphasized in Chapter 24.

**How to run**:

```bash
cd zh-CN/demos/experiments/fab_ontology_text2sql
pip install -r requirements.txt
streamlit run app.py
```

Dependencies are minimal (about 5 packages) and the experiment runs fully offline. Once you configure an API key, you can switch to LLM mode and compare the output differences between the "rule-based fallback" and "LLM template selection" paths.

**What to observe**: enter a natural-language query such as "recent defect records for lot W80" in the UI, and watch how the system first matches ontology concepts, then selects a template, and finally generates SQL — note that no free-form text-concatenated SQL is produced at any point.

## 27.4 Experiment 2: Wafer Fab Ontology MVP — Ontology-Graph-Driven Root Cause Analysis Agent (wafer_ontology_mvp)

**Related Chapters**: Ch. 24/25 (Ontology), Ch. 2 (Agent), Ch. 14 (Knowledge Graph)

**What you'll learn**: this experiment turns the "Object–Link–Action" three-layer ontology mapping from Chapter 24 into a runnable root cause analysis (RCA) system:

- **Ontology layer**: NetworkX + SQLite build an entity-and-relationship graph over Lot/Wafer/Equipment/Defect, providing the data foundation for Palantir's three-layer mapping
- **Reasoning layer**: a LangGraph-driven ReAct Agent traverses, retrieves, and attributes causes on the ontology graph via tool calls
- **Service layer**: FastAPI exposes ontology query APIs; Flask provides a web UI

**How to run**:

```bash
cd zh-CN/demos/experiments/wafer_ontology_mvp
pip install fastapi uvicorn sqlmodel networkx langchain langchain-openai langgraph python-dotenv
python src/main.py      # Start the API service (auto-seeds simulated data)
python web/app.py       # Start the web UI
```

**What to observe**: ask the Agent "Why did yield drop for lots processed on equipment ETCH-A03?" and watch the ReAct loop decompose the question, invoke ontology query tools, trace along the "Equipment → Lot → Wafer → Defect" chain, and finally produce a root-cause conclusion backed by an evidence chain. This is the complete engineering form of knowledge-graph-assisted RCA described in Chapter 14.

## 27.5 Experiment 3: FabGraph — Dual-Graph Data Asset Platform (FabGraph_MVP)

**Related Chapters**: Ch. 14 (Symbolic AI Applications), Ch. 13 (Foundry Service Transformation), Ch. 17 (Fusion Overview)

**What you'll learn**: the most engineering-intensive of the nine experiments, demonstrating "metadata governance + semantic retrieval" for fab data assets:

- **Schema Graph**: a structural graph of tables/columns/types, supporting semantic search and JOIN-path recommendation
- **Lineage Graph**: a data lineage graph that answers "where does this table come from and who uses it"
- **NL2SQL**: natural-language queries grounded in dual-graph context, including graph algorithms such as community detection

**How to run**:

```bash
cd zh-CN/demos/experiments/FabGraph_MVP
pip install -e ".[dev]"
python scripts/init_mock_data.py
uvicorn fabgraph.main:app --host 0.0.0.0 --port 8000 --reload   # API
streamlit run ui/streamlit_app/app.py                             # UI
```

When no API key is configured, the system automatically falls back to mock mode. The project ships with 13 pytest tests that serve as a reference for "how to write tests for a data platform."

**What to observe**: first browse the Schema Graph page to understand how metadata is organized, then ask in natural language "yield trend for the etch process" and watch the system leverage the graph to recommend JOIN paths and generate correct SQL — experience firsthand the technical foundation behind the "Data-as-a-Service" transformation discussed in Chapter 13.

## 27.6 Experiment 4: K8s-Style Declarative Scheduling (C9S_agent)

**Related Chapters**: Ch. 7 (Manufacturing Department / Intelligent Scheduling), Ch. 20 (SA Fusion)

**What you'll learn**: transplant Kubernetes' control-theoretic paradigm (the declarative reconciliation loop) into wafer fab scheduling: the user declares a target (e.g., "daily output of 5,000 wafers"), and four Agents — Supervisor, Scheduler, Worker, and Monitor — continuously reconcile desired state against actual state, eliminating the need for hand-written scheduling scripts. This is a vivid example of the Symbolic + Behavioral (SA) fusion introduced in Chapter 20: the rule system defines goals and constraints, while the behavioral system works to converge toward those goals.

**How to run**:

```bash
cd zh-CN/demos/experiments/C9S_agent
pip install -r requirements.txt   # Only 2 dependencies
python app.py
```

Pure in-memory simulation with no external dependencies; starts in seconds.

**What to observe**: issue an output target on the dashboard and watch the reconciliation loop shrink the gap round by round; then open the "Traditional Pipeline Comparison" page to contrast how the declarative and imperative paradigms respond to disturbances (injected equipment failures).

## 27.7 Experiment 5: Capacity Planning PTA Agent (FabCapacityAgent)

**Related Chapters**: Ch. 10 (Capacity Ramp-Up & Capacity Planning)

**What you'll learn**: the most thoroughly documented, tested, and degradation-strategy-equipped project among the nine experiments, demonstrating capacity analysis orchestrated by four Agents following the "Perception–Thinking–Action" pattern:

- **Real-time monitoring**: dashboards for OEE, UPH, and other metrics (simulated MES data for 90 days across 120 equipment units is auto-generated on first run)
- **Bottleneck detection**: bottleneck localization based on queuing theory and utilization rates
- **What-If simulation**: Monte Carlo simulation of capacity impact for scenarios such as adding equipment, increasing speed, or expanding shifts
- **Agent workbench**: run the full pipeline or debug individual Agents; auto-generates analysis reports

**How to run**:

```bash
cd zh-CN/demos/experiments/FabCapacityAgent/fab_capacity_agent
pip install -r requirements.txt
streamlit run app.py
```

First startup takes 30–60 seconds to generate simulated data. Without an API key, LLM-related features gracefully degrade while core computation remains unaffected. Includes 23 unit tests (`pytest tests/`).

**What to observe**: on the What-If page, simulate "+1 bottleneck equipment" versus "10% speed-up at the bottleneck step" separately, and compare their impact on monthly output — a tangible illustration of the "find the bottleneck first, then decide investment" capacity planning methodology from Chapter 10.

## 27.8 Experiment 6: LoRA Fine-Tuning — Small-Model-Assisted Two-Stage Query Enhancement (fab_llm_fine_tuning)

**Related Chapters**: Ch. 15 (Connectionist AI Applications), Ch. 17 (Fusion Overview)

**What you'll learn**: the ideal companion experiment to the fine-tuning chapter, walking through the complete pipeline of "data synthesis → LoRA training → inference → quantitative evaluation." The core idea is a **two-stage division of labor**: first, a LoRA-fine-tuned Qwen2-0.5B small model handles domain query preprocessing (terminology completion, intent clarification); then a general-purpose large model generates the final SQL — achieving domain adaptation at minimal cost.

**How to run**:

```bash
cd zh-CN/demos/experiments/fab_llm_fine_tuning
pip install -r requirements.txt
python -m fab_mvp.data_generation              # Generate / inspect training data
python -m fab_mvp.train_lora --smoke --epochs 1   # Smoke test (quick pipeline validation)
python -m fab_mvp.train_lora --epochs 3        # Full training
```

The repository already includes training data and evaluation results (`fab_mvp/outputs/`), so you can review the evaluation report without running training. Full training requires downloading the Qwen2-0.5B base model (~1 GB); it runs on CPU but is slow.

**What to observe**: compare the pre- and post-fine-tuning metrics in `outputs/eval_summary.json` to understand why "small-model preprocessing" improves end-to-end accuracy — an extension of the "AI acceleration in data-scarce scenarios" theme from Chapter 15 into the LLM era.

## 27.9 Experiment 7: RTD Real-Time Dispatching & Human-AI Collaboration (fab_ai_rtd_mvp)

**Related Chapters**: Ch. 8 (Process / Equipment Engineering), Ch. 11 (Construction & Ramp-Up Phase), Ch. 22 (LLM Applications)

**What you'll learn**: the only experiment that fully demonstrates "human approval + audit trail," covering the complete RTD (Real-Time Dispatching) dispatching pipeline:

Perception (anomaly detection) → RAG diagnosis (retrieving historical resolution plans) → scheduling recommendation → simulation verification → **L1–L4 tiered human approval** → execution & audit log

Tiered approval is the key to production deployment: low-risk actions are auto-approved, while high-risk actions require human confirmation — this is the engineering answer to both "human-AI collaboration during the construction phase" (Chapter 11) and "trust thresholds for deploying LLMs in fabs" (Chapter 22).

**How to run**:

```bash
cd zh-CN/demos/experiments/fab_ai_rtd_mvp
pip install -r requirements.txt
streamlit run app.py
```

Configuring a DeepSeek/Qwen API key enables real LLM-powered diagnosis; without a key, the entire pipeline runs with rule-based fallback, and the approval and audit workflows remain fully functional.

**What to observe**: trigger an equipment anomaly and follow the UI through the entire pipeline, paying special attention to the approval nodes — dispatching recommendations at different risk levels pause at different tiers awaiting human decisions, and every decision is logged for traceability.

## 27.10 Experiment 8: CIM Trusted System Red-Blue Adversarial Exercise (wafer-trust-guard)

**Related Chapters**: Ch. 22 (LLM Applications), Ch. 23 (Agent Systems)

**What you'll learn**: an adversarial red-blue exercise that answers "how do we verify that an AI system is trustworthy":

- **Red team**: generates non-compliant Recipes that attempt to bypass controls (simulating attacks and misuse)
- **Blue team**: a four-layer verification defense — static rule validation → Embedding semantic alignment → LLM Judge review → FA memory loop (historical case recall)

The four defense layers map directly to the "rules + vectors + large model" hybrid verification approach from the neuro-symbolic discussion in Chapter 18, making this a rare companion experiment for the governance and trust themes.

**How to run**:

```bash
cd zh-CN/demos/experiments/wafer-trust-guard
pip install -r requirements.txt
streamlit run app.py
```

The full pipeline includes mock fallbacks and runs completely without an API key.

**What to observe**: watch where the same non-compliant Recipe gets intercepted across the four defense layers — some are blocked immediately by static rules, while others pass through until the LLM Judge identifies them. Ask yourself: if only one layer were kept, where would the system fail?

## 27.11 Experiment 9: Multi-Agent Evaluation Framework (fab_agent_test)

**Related Chapters**: Ch. 2 (Brief History of AI / Agent Concepts), Ch. 21 (NSA Full Fusion)

**What you'll learn**: answers the question "how do we evaluate whether an Agent system is good?" Four hand-written modules — Planner, ToolSet, Reflector, and Orchestrator — collaborate to perform defect RCA while **evaluating in real time** across three metric categories:

- **Process quality**: task decomposition soundness, tool-call correctness rate
- **Resource cost**: number of invocation rounds, latency
- **System resilience**: inject 30% timeout faults and observe whether the system recovers and completes the task

Zero external AI dependencies (pure mock), white-box implementation — the best starting point for understanding Agent evaluation methodology.

**How to run**:

```bash
cd zh-CN/demos/experiments/fab_agent_test
pip install streamlit
streamlit run app.py
```

**What to observe**: run a full evaluation and focus on the resilience test segment — when tool calls time out, watch how the Orchestrator's retry and degradation strategies kick in, and how the evaluation metrics reflect system state in real time.

## 27.12 Experiment 10: Yield Modeling & Ramp Simulation (yield_modeling_ramp)

Corresponds to **Chapter 9 (Yield Ramp)** and **Chapter 11 (Construction/Ramp Phase)**. A pure-Python implementation of three concepts: Poisson / Negative Binomial / Murphy yield model comparison, S-curve ramp with learning rates, and a starter virtual metrology predictor from FDC signals. It produces three figures and a console comparison, making `Y = exp(-D₀A)` and the "Valley of Death" tangible. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/yield_modeling_ramp
pip install numpy matplotlib scikit-learn
python yield_modeling_ramp.py
```

## 27.13 Experiment 11: Predictive Maintenance RUL (predictive_maintenance_rul)

Corresponds to **Chapter 12 (Mature Mass Production · Predictive Maintenance)**. Uses synthetic equipment-degradation data to predict Remaining Useful Life (RUL) and compares the maintenance cost of "periodic PM" vs "predictive maintenance" — answering the core mature-phase question: when exactly should maintenance happen? Code and docs are bilingual (EN/ZH).

```bash
cd experiments/predictive_maintenance_rul
pip install numpy matplotlib scikit-learn
python predictive_maintenance_rul.py
```

## 27.14 Experiment 12: LLM RAG for Process-Spec QA (llm_rag_spec_qa)

Corresponds to **Chapter 22 (LLMs in Wafer Fabs)**. Implements a minimal RAG system: retrieve relevant snippets from a process-spec (SPEC) document library, then let an LLM generate a cited answer. Uses the DeepSeek API by default; falls back to a Mock LLM when no API key is configured, so it runs offline. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/llm_rag_spec_qa
pip install requests
echo "DEEPSEEK_API_KEY=your_key" > .env   # optional; Mock LLM otherwise
python llm_rag_spec_qa.py
```

## 27.15 Experiment 13: CNN Wafer Defect Classification (wafer_defect_cnn)

Corresponds to **Chapter 15 (Connectionism in the Wafer Fab)**. Generates synthetic wafer maps of four defect patterns (center / edge-ring / cluster / none) and classifies them with a neural network (MLP mirroring CNN, GPU-free), visualizing samples, a confusion matrix, and predictions. The Web UI supports interactive "generate & predict". Code and docs are bilingual (EN/ZH).

```bash
cd experiments/wafer_defect_cnn
pip install numpy matplotlib scikit-learn flask
python wafer_defect_cnn.py        # CLI
python web_app.py                 # Web UI http://127.0.0.1:5003
```

## 27.16 Experiment 14: Q-Learning Dispatch (rl_dispatch_basic)

Corresponds to **Chapter 16 (Behaviorism in the Wafer Fab)** and Chapter 12 (Smart Scheduling). Implements a micro dispatch environment (fast/slow tools, random arrivals), learns a dispatch policy with Q-Learning, compares total reward against random dispatch, and visualizes learning curves and a Gantt chart. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/rl_dispatch_basic
pip install numpy matplotlib flask
python rl_dispatch_basic.py       # CLI
python web_app.py                 # Web UI http://127.0.0.1:5004
```

## 27.17 Experiment 15: Expert-System Defect Diagnosis (expert_system_rca)

Corresponds to **Chapter 14 (Symbolism in the Wafer Fab)**. Implements a forward-chaining expert system: engineers' defect-to-root-cause experience encoded as IF-THEN rules; given observed facts, it infers a confident diagnosis and advice, visualizing the inference chain. The Web UI supports interactive fact selection. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/expert_system_rca
pip install numpy matplotlib flask
python expert_system_rca.py       # CLI
python web_app.py                 # Web UI http://127.0.0.1:5005
```

## 27.18 Experiment 16: LLM Agent with Tool Use (llm_agent_tool_use)

Corresponds to **Chapter 23 (Agent Systems in the Wafer Fab)**. Implements a ReAct (Reasoning+Acting) Agent: the LLM autonomously calls tools (WIP / tool status / utilization / specs), reasons from results, and produces a final answer — the full perceive→plan→act→observe loop. Supports DeepSeek API and offline Mock. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/llm_agent_tool_use
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=your_key" > .env   # optional
python llm_agent_tool_use.py       # CLI
python web_app.py                  # Web UI http://127.0.0.1:5006
```

## 27.19 Experiment 17: Chain-of-Thought RCA (llm_chain_of_thought_rca)

Corresponds to **Chapter 18 (NB Neuro-Symbolic Fusion)**. Guides the LLM to reason step by step — observe → hypothesize → verify → conclude — over yield root causes, then verifies the conclusion with IF-THEN symbolic rules, demonstrating neural+symbolic combination and arbitration. Supports DeepSeek API and offline Mock. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/llm_chain_of_thought_rca
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=your_key" > .env   # optional
python llm_chain_of_thought_rca.py  # CLI
python web_app.py                  # Web UI http://127.0.0.1:5007
```

## 27.20 Experiment 18: LLM Yield Report Automation (llm_report_automation)

Corresponds to **Chapter 22 (LLMs in Wafer Fabs · yield report generation)**. Feeds structured yield data (weekly trend, defect TOP, tool status) to the LLM, which writes a professional yield weekly report (data→text), alongside data charts. Supports DeepSeek API and offline Mock. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/llm_report_automation
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=your_key" > .env   # optional
python llm_report_automation.py    # CLI
python web_app.py                  # Web UI http://127.0.0.1:5008
```

## 27.21 Experiment 19: Multi-Agent Collaboration (multi_agent_collaboration)

Corresponds to **Chapter 23 (multi-agent architecture)**. Simulates fab multi-agent collaboration: a Coordinator agent consults four specialists — process, equipment, yield, dispatch — and synthesizes their opinions into a final decision, demonstrating cross-department orchestration. Supports DeepSeek API and offline Mock. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/multi_agent_collaboration
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=your_key" > .env   # optional
python multi_agent_collaboration.py  # CLI
python web_app.py                  # Web UI http://127.0.0.1:5009
```

## 27.22 Experiment 20: Agent Task Decomposition & Execution (agent_task_decomposition)

Corresponds to **Chapter 17 (SA Symbolic-Action Fusion)** and Chapter 23 (Agent planning). Implements a plan-then-execute Agent: decomposes a high-level goal into executable subtasks, runs each via tools, and synthesizes a completion report — "symbolic planning gives direction, action execution lands it". Supports DeepSeek API and offline Mock. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/agent_task_decomposition
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=your_key" > .env   # optional
python agent_task_decomposition.py  # CLI
python web_app.py                  # Web UI http://127.0.0.1:5010
```

## 27.23 Experiment 21: Reflexion Agent (reflexion_agent)

Corresponds to **Chapter 23 (Agent self-improvement)**. Implements the Reflexion loop: the Agent attempts a load-balancing dispatch problem, evaluates, reflects on its failure, and retries with the reflection, improving round by round — demonstrating Agent self-improvement. Supports DeepSeek API and offline Mock. Code and docs are bilingual (EN/ZH).

```bash
cd experiments/reflexion_agent
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=your_key" > .env   # optional
python reflexion_agent.py          # CLI
python web_app.py                  # Web UI http://127.0.0.1:5011
```

## 27.24 From Experiments to Production: Adaptation Guide

All experiments in this chapter are MVPs. Moving to a production environment typically requires the following adaptations (see each experiment's README for complete design documentation):

1. **Data integration**: replace the simulated data generators with real MES/EAP/SPC data interfaces, keeping the ontology/graph schema stable
2. **Secret management**: migrate API keys from `.env` files to an enterprise secret management system, allocated on a least-privilege basis
3. **Evaluation closed loop**: refer to the three-dimensional evaluation framework in 27.11 to establish continuous evaluation for every deployed Agent
4. **Approval & audit**: for systems that trigger production actions, adopt the tiered approval and audit log design from 27.9
5. **Trust verification**: for systems that provide decision recommendations externally, run pre-launch exercises using the red-blue adversarial approach from 27.10

> Experiments are a shortcut to understanding — and a starting point for questioning. After running them end-to-end, ask yourself: if the real data distribution in a wafer fab differs from the simulated data, which component of this system would fail first? — That is precisely the first threshold between a demo and a production deployment.

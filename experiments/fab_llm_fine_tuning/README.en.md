# 🔬 Fab LLM Two-Stage Query-Enhancement MVP

> Use a fine-tuned **small model (0.5B)** for domain query pre-processing, injecting fab-structured context into a **strong model (DeepSeek)** to generate more accurate SQL and analysis answers.

## Core Idea

Fab engineers often ask in colloquial language or jargon ("What's going on with Tool 3's yield dropping so fast?"). Feeding this directly to a strong model produces generic, imprecise SQL because it lacks domain knowledge (table names, abbreviations, SOPs).

This project solves the problem with a **two-stage architecture**:

```
User colloquial question
    │
    ▼
┌──────────────────────────────┐
│  Stage 1: Fine-tuned small   │  ← LoRA fine-tuning of Qwen2-0.5B
│  model (0.5B)                │
│  Pre-processes into         │
│  structured JSON             │
│  (intent/entities/hints/SQL) │
└──────────┬───────────────────┘
           │ structured context
           ▼
┌──────────────────────────────┐
│  Stage 2: Strong model       │  ← uses the context to generate accurate SQL
│  (DeepSeek)                  │
│  Generates final SQL /       │
│  analysis answer             │
└──────────────────────────────┘
```

**Three pre-processing modes** (one fine-tuned model supports all):

| Mode | Function | Example output |
|------|------|---------|
| `mode_a` domain-aware enhancement | Extracts intent/entities/domain hints/enhanced query | `{"intent":"yield_analysis", "entities":{"eqp_id":"EQP-003"}, ...}` |
| `mode_b` term translation | Colloquial/jargon → professional terminology | `{"translated":"query CP yield of equipment EQP-003..."}` |
| `mode_c` SQL template routing | Matches SQL templates in the knowledge base | `{"template_id":"SQL_TMPL_YIELD_01", "params":{...}}` |

## Project Structure

```
fab_llm_fine_tuning/
├── Qwen2-0.5B/                  # Base model (downloaded from HuggingFace)
├── .env                         # DEEPSEEK_API_KEY
├── requirements.txt
├── fab_mvp/
│   ├── knowledge_base.py        # Fab knowledge base (7 tables/35 abbreviations/8 SQL templates/5 SOPs)
│   ├── data_generation.py       # Synthesizes training data with DeepSeek
│   ├── train_lora.py            # LoRA fine-tuning (one model, mixed training of three modes)
│   ├── inference.py             # Small-model inference (lazy loading, robust JSON parsing)
│   ├── agent.py                 # LangGraph orchestration (enhanced path vs direct path)
│   ├── app.py                   # Streamlit UI
│   ├── eval_cases.py            # 10 evaluation cases
│   ├── eval_runner.py           # Evaluation experiment script (automated metric comparison)
│   ├── data/
│   │   ├── train.jsonl          # 120 training samples (three-mode labeled)
│   │   └── eval.jsonl           # 30 evaluation samples
│   └── outputs/
│       └── lora_adapter/        # Fine-tuned LoRA adapter
```

## Quick Start

### 1. Environment Setup

```bash
# After cloning the project, create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
DEEPSEEK_API_KEY=sk-your-api-key-here
```

### 3. Download the Base Model

Download the Qwen2-0.5B model into the `Qwen2-0.5B/` folder in the project root:

```bash
# Option 1: huggingface-cli
huggingface-cli download Qwen/Qwen2-0.5B --local-dir Qwen2-0.5B

# Option 2: git lfs
git lfs install
git clone https://huggingface.co/Qwen/Qwen2-0.5B
```

### 4. Synthesize Training Data (optional; skip if data already exists)

```bash
python -m fab_mvp.data_generation
# Generates fab_mvp/data/train.jsonl (120 samples) and eval.jsonl (30 samples)
```

### 5. LoRA Fine-Tuning

```bash
# Full training (120 samples × 3 modes = 360 rows, 3 epochs)
python -m fab_mvp.train_lora --epochs 3

# Quick verification (9 rows, 1 epoch)
python -m fab_mvp.train_lora --smoke --epochs 1

# Limit sample count (e.g., use only 60 original samples)
python -m fab_mvp.train_lora --limit 60 --epochs 3
```

**Fine-tuning parameters**:

| Parameter | Default | Description |
|------|--------|------|
| `--epochs` | 3.0 | Number of training epochs |
| `--lr` | 2e-4 | Learning rate |
| `--batch` | 4 | Batch size per device |
| `--grad-accum` | 4 | Gradient accumulation steps |
| `--lora-r` | 16 | LoRA rank |
| `--smoke` | - | Smoke test (only 9 rows) |
| `--limit` | 0 | Limit original sample count |

> **CPU training tip**: 0.5B + LoRA can run on CPU, but slowly (~4–5 min/step). It is recommended to train at least 2–3 epochs so the model learns the JSON output format.

### 6. Inference Verification

```bash
python -m fab_mvp.inference
# Runs the three modes on test questions and prints the JSON outputs
```

### 7. Agent Comparison Verification

```bash
python -m fab_mvp.agent "why did tool 3 yield drop so fast yesterday"
# Runs both the enhanced path and the direct path side by side and compares the outputs
```

### 8. Launch the Web UI

```bash
python -m streamlit run fab_mvp/app.py
# Visit http://localhost:8501 in the browser
```

### 9. Evaluation Experiment

```bash
# 10 cases × 2 paths compared (uses standard JSON to simulate an ideal small model, isolating small-model quality issues)
python -m fab_mvp.eval_runner --n 10 --mode mode_a
```

## Knowledge Base

[knowledge_base.py](fab_mvp/knowledge_base.py) simulates fab domain knowledge and contains four parts:

| Module | Content | Count |
|------|------|------|
| `FAB_SCHEMA` | Table structure + field "de-obfuscation" | 7 tables |
| `GLOSSARY` | Abbreviation dictionary (CP/FT/WAT/SPC/OOC/PM...) | 35 entries |
| `SQL_TEMPLATES` | Analytical SQL template library | 8 templates |
| `SOP_SNIPPETS` | SOP process snippets | 5 entries |

**7 tables**: `WIP_LOT` (work-in-process lots), `EQUIPMENT` (equipment master data), `PROCESS_LOG` (process logs), `YIELD_SUMMARY` (yield summary), `DEFECT_DATA` (defect coordinates), `OOC_ALARM` (SPC alarms), `RECIPE` (recipes)

**8 SQL templates**: yield anomaly query, equipment-related lots, defect hotspot analysis, lot traceability, SPC alarm query, before/after PM comparison, process-parameter deviation, Hold lot query

## Evaluation Results

Using `eval_runner.py` to compare 10 test cases (using standard JSON to simulate ideal small-model output, isolating small-model quality issues):

| Metric | Enhanced path | Direct path | Delta | Enhanced wins |
|------|---------|---------|------|--------|
| **Knowledge-base table-name references** | 2.60 | 0.40 | +2.20 | 9/10 |
| **Entity hit rate** | 86% | 54% | +32% | 7/10 |
| Template accuracy | 10% | 0% | +10% | - |

**Conclusion**: structured context turns the strong model from "scattershot guessing" into "precisely referencing knowledge-base table names and entities". The enhanced path wins 9/10 on knowledge-base table-name references, with a 32-point improvement in entity hit rate.

## Tech Stack

| Component | Technology | Description |
|------|------|------|
| Base model | Qwen2-0.5B | 0.5B parameters, runs on CPU |
| Fine-tuning method | LoRA (PEFT) | r=16, target=q/k/v/o_proj |
| Training framework | TRL SFTTrainer | Instruction fine-tuning, packing=False |
| Strong model | DeepSeek Chat | Called via the OpenAI-compatible API |
| Orchestration framework | LangGraph | StateGraph dual-path parallel |
| Web UI | Streamlit | Enhanced path vs direct path shown side by side |
| Data synthesis | DeepSeek | Batch-generates training data from the knowledge base |

## Architecture Highlights

1. **Small model does what the big model does poorly**: the 0.5B small model is not responsible for reasoning — only for "narrow but deep" domain-signal amplification (abbreviation decoding, table-name mapping, template routing), leaving reasoning to the strong model.
2. **One model, three modes**: modes are distinguished by instruction prefixes; a single LoRA adapter supports all three pre-processing modes without needing three models.
3. **Consistent training/inference format**: `SYSTEM_PROMPT` + `MODE_PROMPTS` are shared between training and inference, ensuring the fine-tuning takes effect.
4. **Dual-path comparison**: LangGraph runs the enhanced path and the direct path simultaneously, visually demonstrating the incremental value of small-model pre-processing.

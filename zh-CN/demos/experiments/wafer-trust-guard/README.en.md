# 🛡️ wafer-trust-guard — CIM Trusted-System "Red-Team vs Blue-Team" MVP Demo

> **A process Recipe is the chip design code.**
> The Red Team agent is responsible for "cutting corners", while the Blue Team Verifier holds absolute veto power and "historical memory".
> Core belief: **Design is cheap, Verification is everything.**
>
> This system simulates the tape-out verification and FA (Failure Analysis) closed-loop process of TSMC / SMIC.

## Quick Start

```bash
# 1. Configure .env (no code changes needed; keys are always read from the environment):
#    DEEPSEEK_API_KEY=sk-xxx          # DeepSeek (OpenAI SDK compatible)
#    DASHSCOPE_API_KEY=sk-xxx         # Aliyun DashScope (Qwen qwen3.7-text-embedding)
# 2. Install dependencies
pip install -r requirements.txt
# 3. Launch (the failure_log.json knowledge base is auto-generated on first run)
streamlit run app.py
```

## Red-Team / Blue-Team + FA Closed-Loop Flow

1. **Select the adversary mode at the top**: `Normal Agent (mock)` vs `Red-Team Attack Mode (DeepSeek)`;
2. **On the left**, enter the process requirement (Red-Team mode suggests "do a high-temperature diffusion, keep it safe");
3. **In the middle**, click "Generate Recipe": in Red-Team mode, DeepSeek plays a "process engineer who wants to go home early" and generates a Recipe that is **superficially compliant but secretly violating**;
4. **On the right**, the Blue-Team Verifier guards each layer:
   - **📚 Historical failure-base matching**: first queries the FA knowledge base; a similar hit immediately raises an alert (⚠️ N similar recipes were blocked historically);
   - **L1 static gate**: physical temperature limits, gas whitelist, Pydantic field types;
   - **Embedding intent alignment**: Qwen `qwen3.7-text-embedding` cosine similarity, `< 0.7` means "intent deviation" (`st.progress` shows the alignment score);
   - **LLM-as-Judge**: DeepSeek plays a senior PE, injecting historical cases as Few-Shot, with a reason field marking whether the recipe "hits a historical failure mode";
   - **Final verdict**: `🟢 allow dispatch to tool` / `🔴 intercept (prevent wafer scrap)`;
5. **FA closed loop**: every intercepted violation is automatically written into `failure_log.json` (FA-ID filed and added to the process blacklist); the next similar requirement immediately triggers a historical alert — **the Verifier has "memory"**.

## Directory Structure

```
wafer-trust-guard/
├── app.py                        # Streamlit entry (red-team/blue-team + FA memory UI)
├── config.py                     # .env loading + DeepSeek client (OpenAI SDK compatible)
├── failure/                      # Failure-analysis knowledge base (FA memory)
│   ├── __init__.py
│   ├── embedder.py               # Qwen qwen3.7-text-embedding wrapper (returns zero vector on failure)
│   └── fa_store.py               # FA case store/query (local JSON + cosine retrieval, no Chroma/FAISS)
├── generator/
│   ├── __init__.py
│   ├── mock_agent.py             # Normal mode: 80% compliant / 20% hallucinated (pure local)
│   └── redteam_agent.py          # Red-team mode: DeepSeek generates subtly violating Recipes (local fallback on failure)
├── verifier/
│   ├── __init__.py               # Verdict result types
│   ├── static_rules.py           # L1 static gate (physical limits, whitelist, Pydantic types)
│   ├── alignment_embedding.py    # L2 embedding intent alignment (qwen3.7-text-embedding + cosine similarity)
│   ├── llm_judge.py              # L3 LLM-as-Judge (DeepSeek + historical FA Few-Shot)
│   ├── alignment.py              # (reserved) rule-based intent alignment
│   └── invariants.py             # (reserved) attribute invariants
├── schemas/
│   ├── __init__.py
│   └── recipe.py                 # Pydantic Recipe data contract
├── failure_log.json              # Auto-generated local FA knowledge base (gitignored)
├── requirements.txt
└── README.md
```

## FA Knowledge Base (FA Memory) Design

- **Storage**: local `failure_log.json` (vectors stored as JSON files; the MVP avoids Chroma/FAISS and never loses data);
- **Vectorization**: `failure/embedder.py` uses Qwen `qwen3.7-text-embedding`, returning a zero vector on failure without errors;
- **Ingestion**: `fa_store.add_case(req, recipe, reason, layer)`, text = `Requirement: {req}. Violation reason: {reason}`;
- **Retrieval**: `fa_store.search(req, top_k=3)` — cosine similarity ≥ 0.6 counts as "similar history";
- **Few-Shot**: `llm_judge.py` injects historical cases into the System Prompt, reminding the senior PE "the last time this was done it blew up";
- **On first run, 3 mock FA profiles are auto-seeded** (high-temperature diffusion over-temperature / wrong gas used in cleaning / etch time too short).

## Design Notes

- **Never hardcode API keys**: all keys are read from `.env` via `config.py`;
- **All LLM calls are wrapped in try/except with mock fallback**: if either DeepSeek or DashScope is unavailable, the Demo degrades to local rules without crashing;
- **Physical isolation**: the Generator (including the red team) never imports any verifier / failure code — **the designer does not know the verification history**;
- **UI constraints**: only native Streamlit components (`st.json` / `st.progress` / `st.expander` / `st.success` / `st.error`), no custom CSS/HTML;
- The red-team module is for demonstration and verification-layer stress testing only, never for any real production environment.

## Disclaimer

This project is a teaching-demo MVP: red-team behaviors are simulated scenarios, and verification rules and FA data are examples; a real CIM system must combine equipment manuals, process-engineering specifications, and simulation data.

# 🔬 思维链良率根因分析 (Chain-of-Thought RCA)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第18章(NB 神经符号融合)**——用**思维链(Chain-of-Thought)**让 LLM 按"观察→假设→验证→结论"分步推理良率问题根因,并用规则/知识校验推理结论(神经+符号)。默认调用 DeepSeek API;未配置 Key 时自动降级为 Mock LLM。

**English Intro** | This experiment corresponds to **Chapter 18 (NB Neuro-Symbolic Fusion)**: a **Chain-of-Thought (CoT)** prompt makes the LLM reason step by step — observe → hypothesize → verify → conclude — over a yield problem, with rule-based verification of the conclusion (neural + symbolic). Uses the DeepSeek API by default; falls back to a Mock LLM without a key.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 用 CoT 提示引导 LLM 分步推理 | Guide the LLM to reason stepwise via CoT |
| 对比直接回答 vs 思维链回答 | Compare direct answer vs CoT answer |
| 用规则校验结论(符号层) | Verify conclusions with rules (symbolic layer) |
| 可视化推理步骤 | Visualize the reasoning steps |

## 🚀 快速开始 / Quick Start

```bash
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可选; 不配置用 Mock
python llm_chain_of_thought_rca.py
python web_app.py     # Web 界面 http://127.0.0.1:5007
```

## 🧠 原理速览 / Theory at a Glance

- **直接回答 / direct**: `问题 → 结论`(易跳步、易幻觉)
- **思维链 CoT**: `问题 → 观察 → 假设 → 验证 → 结论`(可解释、可校验)
- **符号校验 / symbolic check**: 用 IF-THEN 规则(如"边缘环形缺陷 → 光刻焦点偏移")核对 LLM 结论

## 📊 预期输出 / Expected Output

- 控制台: CoT 分步推理 + 符号校验结果
- `output/cot_steps.png` — 推理步骤时间线
- Web 界面: 输入观察事实 → 显示完整推理链

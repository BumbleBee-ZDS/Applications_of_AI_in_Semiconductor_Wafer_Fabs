# 🔬 LLM Agent 工具调用 (LLM Agent with Tool Use)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第23章(Agent 系统在晶圆厂的实践)**。实现一个 **ReAct(推理+行动)Agent**:LLM 自主决定调用哪些工具(查询WIP、查设备状态、算利用率、查工艺规格),执行工具后根据结果继续推理,直到给出最终回答。完整演示"感知→规划→行动→观察"的 Agent 循环。默认调用 DeepSeek API;未配置 Key 时自动降级为 Mock LLM。

**English Intro** | This experiment corresponds to **Chapter 23 (Agent Systems in the Wafer Fab)**. It implements a **ReAct (Reasoning + Acting) Agent**: the LLM autonomously decides which tools to call (query WIP, check tool status, compute utilization, look up specs), continues reasoning from tool results until reaching a final answer — the full "perceive → plan → act → observe" loop. Uses the DeepSeek API by default; falls back to a Mock LLM without a key.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 为 LLM 提供可调用的工具集 | Provide a tool set the LLM can call |
| 实现 ReAct 循环(行动→观察→再推理) | Implement the ReAct loop (act → observe → reason) |
| 可视化工具调用轨迹 | Visualize the tool-call trace |
| 支持 API 与 Mock 双模式 | Support both API and Mock modes |

## 🚀 快速开始 / Quick Start

```bash
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可选; 不配置用 Mock
python llm_agent_tool_use.py
python web_app.py     # Web 界面 http://127.0.0.1:5006
```

## 🧠 原理速览 / Theory at a Glance

```
问题 → [LLM 思考: 需要哪个工具?] → 调用工具 → 得到结果
   ↑                                                ↓
   └────────── 继续推理 ←──── 结果回填 ←─────────────┘
   (直到 LLM 输出最终答案)
```

## 📊 预期输出 / Expected Output

- 控制台: 每个问题的工具调用轨迹(步骤、工具、参数、结果摘要)
- `output/agent_trace.png` — 工具调用轨迹图
- Web 界面: 输入问题 → 可视化调用链与最终回答

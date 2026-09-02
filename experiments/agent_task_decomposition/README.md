# 🔬 Agent 任务分解与执行 (Task Decomposition & Execution)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第17章(SA 符号行为融合)**与第23章 Agent 规划组件。实现**规划-执行型 Agent**:把高层目标("提升某层良率")自动分解为可执行的子任务,再逐一调用工具执行,最后汇总为完成报告——演示"符号规划做方向,行为执行做落地"的 SA 融合思想。

**English Intro** | This experiment corresponds to **Chapter 17 (SA Symbolic-Action Fusion)** and Chapter 23 (Agent planning). It implements a **plan-then-execute Agent**: decomposes a high-level goal ("improve yield of a layer") into executable subtasks, executes each via tool calls, and synthesizes a completion report — demonstrating "symbolic planning gives direction, action execution lands it" (SA fusion).

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 用 LLM/规则把目标分解为子任务 | Decompose a goal into subtasks (LLM/rules) |
| 为每个子任务匹配工具并执行 | Match tools to subtasks and execute them |
| 汇总为完成报告 | Synthesize a completion report |
| 可视化任务分解树 | Visualize the task-decomposition tree |

## 🚀 快速开始 / Quick Start

```bash
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可选; 不配置用 Mock
python agent_task_decomposition.py
python web_app.py     # Web 界面 http://127.0.0.1:5010
```

## 🧠 原理速览 / Theory at a Glance

```
目标 goal: "提升光刻层良率"
  ├─ 子任务1: 收集良率数据   → 工具 query_yield_data
  ├─ 子任务2: 缺陷模式分析   → 工具 analyze_wafermap
  ├─ 子任务3: 参数相关性分析 → 工具 analyze_fdc
  ├─ 子任务4: 给出优化建议   → 工具 suggest_actions
  └─ 汇总报告
```

## 📊 预期输出 / Expected Output

- 控制台: 任务分解 + 每步执行结果 + 完成报告
- `output/task_tree.png` — 任务分解树
- Web 界面: 输入目标 → 任务树与执行结果

# 🔬 反思型 Agent (Reflexion Agent)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第23章(Agent 系统在晶圆厂的实践)**。实现 **Reflexion(反思)循环**:Agent 尝试解决一个负载均衡派工问题 → 评估表现 → **自我反思**失败原因 → 带着反思重试,逐步改进——演示 Agent 的自我改进机制。默认调用 DeepSeek API;未配置 Key 时自动降级为 Mock 规则反思。

**English Intro** | This experiment corresponds to **Chapter 23 (Agent Systems in the Wafer Fab)**. It implements a **Reflexion loop**: the Agent attempts a load-balancing dispatch problem → evaluates its performance → **reflects on the failure** → retries with the reflection, improving step by step — demonstrating Agent self-improvement. Uses the DeepSeek API by default; falls back to rule-based Mock reflection.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 定义可评估的 Agent 任务 | Define an evaluable agent task |
| 实现"执行→评估→反思→重试"循环 | Implement the act → evaluate → reflect → retry loop |
| 可视化每轮改进 | Visualize improvement per round |
| 支持 API 与 Mock 双模式 | Support both API and Mock modes |

## 🚀 快速开始 / Quick Start

```bash
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可选; 不配置用 Mock
python reflexion_agent.py
python web_app.py     # Web 界面 http://127.0.0.1:5011
```

## 🧠 原理速览 / Theory at a Glance

```
任务(负载均衡派工)
  ↓ 尝试方案
评估(最大完工时间/负载均衡度)
  ↓ 不达标
反思(LLM: 为什么差? 怎么改?) → 携带反思重试
  ↓ 达标或达轮次上限
最终方案
```

## 📊 预期输出 / Expected Output

- 控制台: 每轮方案、评估分、反思内容
- `output/reflexion_curve.png` — 每轮负载均衡度下降曲线
- Web 界面: 迭代过程可视化

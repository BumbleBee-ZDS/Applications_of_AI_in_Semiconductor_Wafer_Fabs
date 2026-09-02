# 🔬 多 Agent 协作诊断 (Multi-Agent Collaboration)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第23章(Agent 系统在晶圆厂的实践·多 Agent 架构)**。模拟晶圆厂的**多 Agent 协作**:主持人(Coordinator)Agent 收到质量问题后,分别咨询工艺、设备、良率、调度四个专业 Agent,收集各自意见后汇总为最终决策——演示跨部门协同的 Agent 编排。

**English Intro** | This experiment corresponds to **Chapter 23 (Agent Systems in the Wafer Fab · multi-agent architecture)**. It simulates **multi-agent collaboration** in a fab: a Coordinator agent, upon receiving a quality problem, consults four specialist agents — process, equipment, yield, and dispatch — then synthesizes their opinions into a final decision, demonstrating cross-department agent orchestration.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 定义多个专业 Agent(角色分工) | Define specialist agents (role separation) |
| 实现主持人编排(咨询→汇总) | Implement coordinator orchestration (consult → synthesize) |
| 可视化协作流程 | Visualize the collaboration flow |
| 支持 API 与 Mock 双模式 | Support both API and Mock modes |

## 🚀 快速开始 / Quick Start

```bash
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可选; 不配置用 Mock
python multi_agent_collaboration.py
python web_app.py     # Web 界面 http://127.0.0.1:5009
```

## 🧠 原理速览 / Theory at a Glance

```
用户问题 → [主持人 Agent] ──┬→ 工艺 Agent → 工艺视角意见
                            ├→ 设备 Agent → 设备视角意见
                            ├→ 良率 Agent → 数据视角意见
                            └→ 调度 Agent → 产线视角意见
                              ↓ 汇总
                          [最终综合决策]
```

## 📊 预期输出 / Expected Output

- 控制台: 各 Agent 意见 + 主持人最终决策
- `output/agent_collab.png` — 多 Agent 协作流程图
- Web 界面: 选择问题 → 各 Agent 意见与最终决策

# 🔬 Q-Learning 智能派工 (Reinforcement-Learning Dispatch)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第16章(行为主义在晶圆厂的应用)**与第12章智能排程。实现一个微型晶圆厂派工环境（2台设备、随机到达的批次），用 **Q-Learning** 学习最优派工策略，并与"贪心派工"对比，可视化学习曲线与调度甘特图。

**English Intro** | This experiment corresponds to **Chapter 16 (Behaviorism in the Wafer Fab)** and Chapter 12 (Smart Scheduling). It implements a micro fab dispatch environment (2 tools, randomly arriving lots) and trains a **Q-Learning** dispatch policy, comparing it against greedy dispatch with learning curves and Gantt charts.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 建立"状态-动作-奖励"的派工 MDP | Model dispatch as an MDP (state-action-reward) |
| 用 Q-Learning 学习派工策略 | Learn a dispatch policy via Q-Learning |
| 与贪心策略对比总等待时间 | Compare total waiting time vs greedy |
| 可视化学习曲线与甘特图 | Visualize learning curves and a Gantt chart |

## 🚀 快速开始 / Quick Start

```bash
pip install numpy matplotlib
python rl_dispatch_basic.py
# Web 界面 / Web UI:
python web_app.py     # http://127.0.0.1:5004
```

## 🧠 原理速览 / Theory at a Glance

- **状态 state**：两台设备的队列长度 `(q0, q1)`
- **动作 action**：将到达批次派给设备 0 或设备 1
- **奖励 reward**：批次处理完成获得正奖励，排队等待付出时间成本
- **Q 更新 / Q update**：`Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') − Q(s,a)]`

## 📊 预期输出 / Expected Output

- `output/learning_curve.png` — 每回合平均等待时间随训练下降
- `output/gantt.png` — Q 策略 vs 贪心策略的调度甘特图

# 🔬 良率模型与爬坡模拟 (Yield Modeling & Ramp Simulation)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第9章(良率爬坡)**与**第11章(建设期与爬坡期)**。通过 Python 动手实现三大核心概念：经典良率统计模型（Poisson / 负二项式）、S 形良率爬坡曲线与学习率、以及虚拟量测（Virtual Metrology）的入门预测。

**English Intro** | This experiment corresponds to **Chapter 9 (Yield Ramp)** and **Chapter 11 (Construction & Ramp Phase)** of *AI Applications in Semiconductor Wafer Fabs*. You will implement, step by step: classic yield statistical models (Poisson / Negative Binomial), the S-shaped yield ramp curve with learning rates, and a starter Virtual Metrology (VM) predictor.

---

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 用代码理解 `Y = exp(-D₀·A)` 的数学含义 | Understand `Y = exp(-D₀·A)` in code |
| 对比 Poisson 与负二项式模型（聚集缺陷） | Compare Poisson vs Negative Binomial (clustered defects) |
| 模拟不同学习率下的良率爬坡 S 曲线 | Simulate S-curve yield ramps under different learning rates |
| 用 FDC 传感器数据做虚拟量测入门预测 | Build a starter VM predictor from FDC sensor data |

## 🚀 快速开始 / Quick Start

```bash
pip install numpy matplotlib scikit-learn
python yield_modeling_ramp.py
```

运行后会在 `output/` 生成三张图，并在控制台输出良率模型对比结论。

Output: three figures in `output/` plus a console report comparing yield models.

## 📁 文件结构 / Files

```
yield_modeling_ramp/
├── yield_modeling_ramp.py   # 主程序 Main script
├── requirements.txt
├── README.md                # 本文件 This file
└── output/                  # 生成的图片与报告
```

## 🧠 原理速览 / Theory at a Glance

1. **Poisson 模型 / Poisson model**：`Y = exp(-D₀·A)`，假设缺陷随机分布。
2. **负二项式模型 / Negative Binomial**：`Y = (1 + D₀·A/α)^(-α)`，α 越小，缺陷聚集越严重。
3. **爬坡 S 曲线 / Ramp S-curve**：logistic 函数，学习率（Learning Rate）决定曲线斜率。
4. **虚拟量测 / Virtual Metrology**：用 FDC 传感信号回归预测膜厚等量测结果，实现"免检/抽检"。

## 📊 预期输出 / Expected Output

- `output/yield_models.png` — 三种良率模型随缺陷密度/芯片面积的变化曲线
- `output/ramp_curves.png` — 快/慢学习率的 S 形爬坡曲线与量产目标线
- `output/virtual_metrology.png` — 虚拟量测预测 vs 实际量测

# 🔬 预测性维护 RUL 实验 (Predictive Maintenance RUL)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第12章(成熟量产期·预测性维护)**。通过合成设备退化数据,动手实现剩余寿命(RUL)预测与维护策略对比:定期 PM 与预测性维护哪个更省钱?

**English Intro** | This experiment corresponds to **Chapter 12 (Mature Mass Production · Predictive Maintenance)**. Using synthetic equipment-degradation data, you will implement Remaining Useful Life (RUL) prediction and compare maintenance strategies: periodic PM vs predictive maintenance — which one saves more money?

---

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 生成设备退化信号(振动/RF特征随运行退化) | Generate degradation signals (vibration/RF drift over runtime) |
| 拟合退化模型并预测 RUL | Fit a degradation model and predict RUL |
| 对比"定期PM"与"预测性维护"的停机损失 | Compare downtime cost: periodic PM vs predictive maintenance |

## 🚀 快速开始 / Quick Start

```bash
pip install numpy matplotlib scikit-learn
python predictive_maintenance_rul.py
```

## 📁 文件结构 / Files

```
predictive_maintenance_rul/
├── predictive_maintenance_rul.py
├── requirements.txt
├── README.md
└── output/
```

## 🧠 原理速览 / Theory at a Glance

1. **退化建模 / Degradation modeling**：设备健康特征随运行时间单调退化,越过失效阈值即故障。
2. **RUL 预测 / RUL prediction**：外推退化曲线,估计"距离失效阈值还有多久"。
3. **维护策略 / Maintenance strategy**：
   - 定期 PM:固定间隔停机维护,可能过早(浪费)或过晚(故障)
   - 预测性维护:在 RUL 接近阈值时安排停机,避免非计划停机损失

## 📊 预期输出 / Expected Output

- `output/degradation.png` — 退化曲线与失效阈值、RUL 预测
- `output/cost_comparison.png` — 定期 PM vs 预测性维护的累计成本

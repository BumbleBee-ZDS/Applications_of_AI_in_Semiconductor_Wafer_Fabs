# 🔬 CNN 晶圆缺陷分类 (Wafer Defect Classification)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第15章(连接主义在晶圆厂的应用)**。生成带有不同缺陷模式的模拟晶圆图（中心缺陷 / 边缘环形缺陷 / 簇状缺陷 / 无缺陷），用神经网络（MLP，模拟 CNN 的分类思想）自动分类，并可视化晶圆图样本、混淆矩阵与预测结果。

**English Intro** | This experiment corresponds to **Chapter 15 (Connectionism in the Wafer Fab)**. It generates synthetic wafer maps with different defect patterns (center / edge-ring / cluster / none), classifies them with a neural network (MLP, mirroring CNN classification), and visualizes wafer samples, a confusion matrix, and predictions.

> 说明 / Note: 为了零 GPU 依赖、可在任何机器上运行，本实验用 scikit-learn 的 MLP 分类器实现"数据→模式识别"的核心思想；换用 PyTorch/TensorFlow CNN 只是把分类器替换为卷积网络。
> To stay dependency-light and GPU-free, this experiment uses an MLP from scikit-learn to demonstrate the core "data → pattern recognition" idea; swapping in a PyTorch/TensorFlow CNN is a drop-in classifier replacement.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 生成四种缺陷模式的模拟晶圆图 | Generate wafer maps with 4 defect patterns |
| 训练神经网络自动分类缺陷类型 | Train a neural net to classify defect types |
| 评估分类准确率并可视化混淆矩阵 | Evaluate accuracy and visualize a confusion matrix |

## 🚀 快速开始 / Quick Start

```bash
pip install numpy matplotlib scikit-learn
python wafer_defect_cnn.py
# Web 界面 / Web UI:
python web_app.py     # http://127.0.0.1:5003
```

## 📊 预期输出 / Expected Output

- `output/wafer_samples.png` — 各类缺陷晶圆图样本
- `output/confusion_matrix.png` — 混淆矩阵与准确率
- 控制台报告: 训练/测试准确率

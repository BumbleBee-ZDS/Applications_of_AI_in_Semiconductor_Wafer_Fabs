# 🔬 专家系统缺陷诊断 (Expert-System RCA)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第14章(符号主义在晶圆厂的应用)**。实现一个经典的**前向推理专家系统**：将资深工程师的缺陷-根因经验编码为 IF-THEN 规则，输入缺陷观察事实，自动推理输出根因诊断、置信度与建议措施，并可视化推理链。

**English Intro** | This experiment corresponds to **Chapter 14 (Symbolism in the Wafer Fab)**. It implements a classic **forward-chaining expert system**: encode senior engineers' defect-to-root-cause experience as IF-THEN rules, feed in observed defect facts, and automatically infer a root-cause diagnosis with confidence and recommended actions, visualizing the inference chain.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 用规则表达领域知识(知识获取) | Express domain knowledge as rules |
| 实现前向链接推理引擎 | Implement a forward-chaining inference engine |
| 输出带置信度的诊断与建议 | Output diagnosis with confidence and advice |
| 可视化推理链 | Visualize the inference chain |

## 🚀 快速开始 / Quick Start

```bash
pip install numpy matplotlib
python expert_system_rca.py
# Web 界面 / Web UI:
python web_app.py     # http://127.0.0.1:5005
```

## 🧠 原理速览 / Theory at a Glance

- **规则 Rule**：`IF 前提1 AND 前提2 THEN 结论 (置信度, 建议)`
- **前向推理 / forward chaining**：从已知事实出发，重复匹配可用规则，直到没有新结论
- **冲突消解 / conflict resolution**：置信度最高的规则优先

## 📊 预期输出 / Expected Output

- `output/inference_chain.png` — 推理链(事实→规则→结论)
- 控制台诊断报告: 根因、置信度、建议

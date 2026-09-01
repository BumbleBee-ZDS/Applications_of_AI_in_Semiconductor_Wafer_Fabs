# 🔬 LLM 良率周报自动生成 (LLM Yield Report Automation)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第22章(LLM在晶圆厂的应用·良率分析/报告生成)**。把结构化的良率数据（周趋势、缺陷TOP、设备状态）交给 LLM，自动生成一份专业的良率周报（数据→叙述），并可视化数据图表。默认调用 DeepSeek API；未配置 Key 时自动降级为 Mock LLM。

**English Intro** | This experiment corresponds to **Chapter 22 (LLMs in Wafer Fabs · yield analysis & report generation)**. It feeds structured yield data (weekly trend, defect TOP, tool status) to an LLM, which automatically writes a professional yield weekly report (data → narrative), alongside visualized charts. Uses the DeepSeek API by default; falls back to a Mock LLM without a key.

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 将结构化数据转化为自然语言报告 | Turn structured data into a narrative report |
| 生成含洞察与建议的专业周报 | Generate a professional weekly report with insights & advice |
| 可视化良率趋势与缺陷TOP | Visualize the yield trend and defect TOP |
| 支持 API 与 Mock 双模式 | Support both API and Mock modes |

## 🚀 快速开始 / Quick Start

```bash
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可选; 不配置用 Mock
python llm_report_automation.py
python web_app.py     # Web 界面 http://127.0.0.1:5008
```

## 🧠 原理速览 / Theory at a Glance

- **数据→文本 (Data-to-Text)**: 结构化数据 + 报告框架 → LLM 填充生成
- **关键**: 明确要求"基于数据、不得编造数字、给出可执行建议"

## 📊 预期输出 / Expected Output

- `output/yield_trend.png` — 良率周趋势图
- 控制台 + Web: 自动生成的良率周报全文

# 🏭 fab_rtd_llm_agent_mvp

模拟半导体 **12 英寸晶圆厂 RTD（Real-Time Dispatching）实时派工系统** 被 LLM Agent 增强后的 MVP 项目。
基于 **Python + Streamlit 多页面** 构建，真实调用 **DeepSeek（推理）+ 阿里千问（向量化）** 大模型 API。

## ✨ 功能一览

- 📡 **实时监控**：模拟 8 台设备 / 8 个批次 / PM 计划 / 区域瓶颈负载，支持一键注入 4 种工艺异常
- 🔍 **Agent 全链路**：感知（阈值）→ 诊断（千问 RAG + DeepSeek v4-pro）→ 调度（DeepSeek v4-pro）→ RL 仿真评估
- ✅ **人工审批**：L1~L4 风险分级，L3 需 2 人、L4 需 3 人审批，低风险自动执行
- 📜 **审计日志**：全链路 trace_id 追溯，支持 JSON 导出
- 📚 **知识库**：10 篇工艺知识文档（CVD / 光刻 / 刻蚀 / Q-Time / PM 等），千问 Embedding + 余弦相似度 RAG 检索

## 🧩 Agent 架构

```
感知 Agent(阈值) → 诊断 Agent(千问RAG + DeepSeek v4-pro) → 调度 Agent(DeepSeek v4-pro)
     → RL 仿真(启发式奖励 + 扰动探索) → 执行 Agent(L1~L4 分级 + 审批) → 审计 Agent(全链路日志)
```

| 环节 | 模型 | 说明 |
|---|---|---|
| 诊断 | `deepseek-v4-pro` + `qwen3.7-text-embedding` | RAG 检索 Top-3 知识 → 根因 / 质量影响 / 调度建议 |
| 调度 | `deepseek-v4-pro` | Q-Time / Recipe 兼容 / PM / HOLD 约束下生成派工策略 |
| 向量化 | `qwen3.7-text-embedding` | dimensions=1024，text_type 区分 query/document |

## 🚀 快速开始

### 1. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入真实 Key：
#   DEEPSEEK_API_KEY=sk-xxx
#   DASHSCOPE_API_KEY=sk-xxx
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动

```bash
streamlit run app.py
```

首次启动会自动调用千问 API 向量化知识库（10 篇文档，约 1~2 次 API 调用）。

### 4. 体验流程

1. **1 实时监控**：下拉选择异常场景（温度漂移 / 压力异常 / EPD 丢失 / Overlay 超差）→ 点击「刷新 / 注入」
2. **2 Agent 分析**：点击「运行全链路」，查看感知事件、诊断报告（含置信度进度条与知识库引用）、派工策略、RL 排名
3. **3 人工审批**：L1/L2 自动执行；L3/L4 生成审批单，多人审批通过后执行
4. **4 审计日志**：按 trace_id 追溯全链路，导出 JSON
5. **5 知识库**：任意查询 RAG 检索演示

## 🌡 可注入异常场景

| 场景 | 注入位置 | 感知阈值 |
|---|---|---|
| CVD 温度漂移 | CVD-001 温度 +1.2°C | 偏离配方中心 ≥0.5°C |
| CVD 压力异常 | CVD-003 压力 +22% | 偏离配方中心 ≥15% |
| 刻蚀 EPD 丢失 | ETCH-201 EPD 信号 0.05 | EPD < 0.3 |
| 光刻 Overlay 超差 | LITHO-101 Overlay 9.2nm | 超出规格 3.0nm |

## 🛡 无 Key 优雅降级

未配置 `DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY` 时：
- 诊断 Agent 自动回退**规则式诊断**（并标注降级原因）；
- 调度 Agent 自动回退**启发式贪心派工**；
- 知识库向量化回退**本地哈希伪向量**（RAG 流程仍可演示）；
- RL 仿真、审批、审计完全不受影响。

## 📁 目录结构

```
fab_rtd_llm_agent_mvp/
├── .env.example            # 环境变量模板
├── requirements.txt
├── app.py                  # Streamlit 主页 + 侧边栏
├── data/
│   └── factory_simulator.py # 工厂实时数据模拟器（异常注入）
├── agents/
│   ├── perception_agent.py  # 感知：异常检测
│   ├── diagnosis_agent.py   # 诊断：RAG + DeepSeek 根因分析
│   ├── scheduling_agent.py  # 调度：DeepSeek 派工策略
│   ├── execution_agent.py   # 执行：风险分级 + 审批
│   ├── rl_simulator.py      # RL 仿真评估
│   └── audit_agent.py       # 审计：全链路日志
├── utils/
│   ├── llm_client.py        # DeepSeek + 千问客户端封装
│   ├── knowledge_base.py    # 工艺知识库 + RAG 检索
│   └── helpers.py           # 通用工具、session 初始化
└── pages/                   # Streamlit 多页面
    ├── 1_实时监控.py
    ├── 2_Agent分析.py
    ├── 3_人工审批.py
    ├── 4_审计日志.py
    └── 5_知识库.py
```

## ⚙️ 技术栈

Python 3.10+ · Streamlit ≥1.38 · pandas · numpy · scikit-learn · plotly · openai ≥1.40 · python-dotenv

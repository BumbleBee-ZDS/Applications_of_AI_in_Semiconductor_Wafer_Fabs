# 🏭 FabCapacityAgent — 晶圆厂 AI 产能智能中枢

> Semiconductor Fab Capacity Intelligence Agent
>
> 基于 PTA (Perceive-Think-Act) 循环的轻量级 Agent 框架,实现半导体晶圆厂产能的**实时监控、历史分析、预测规划**。

---

## 📌 项目简介

FabCapacityAgent 是一个面向半导体晶圆制造工厂 (Fab) 的 AI 产能计算 MVP 系统。系统通过 4 个串联的 Agent (感知 → 分析 → 决策 → 执行) 自动完成全厂产能数据的采集、瓶颈诊断、预测仿真和报告生成,帮助产能工程师快速定位瓶颈、评估优化方案。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🧠 **自研 PTA Agent 框架** | 不依赖 LangChain/AutoGen,轻量级 Perceive-Think-Act 循环 |
| 🤖 **LLM 增强 (可选)** | 支持 DeepSeek / Qwen,未配置时自动回退本地模板 |
| 📊 **Streamlit 多页应用** | 深蓝科技风,6 个页面,中文界面 |
| 🗄 **SQLite + 模拟 MES 数据** | 90 天历史 / 120 台设备 / 5~8 万条工序记录,首次运行自动生成 |
| 📈 **Plotly 交互式图表** | OEE / WIP / 趋势 / 热力图 / Pareto / 蒙特卡洛 |
| 🎯 **What-If 仿真** | 加设备 / 调 OEE / PM 优化 / 新产品 / 组合情景 + 风险评估 |

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Windows / macOS / Linux
- (可选) DeepSeek 或 Qwen API Key

### 2. 安装依赖

```bash
cd fab_capacity_agent
pip install -r requirements.txt
```

### 3. (可选) 配置 LLM API Key

在项目根目录 (FabCapacityAgent/.env) 创建 `.env` 文件:

```ini
# DeepSeek API (https://platform.deepseek.com/)
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Aliyun Qwen / DashScope (https://dashscope.console.aliyun.com/)
DASHSCOPE_API_KEY=sk-your-qwen-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

> **未配置时**:系统自动回退到本地统计模型/模板,功能不受影响。

### 4. 启动应用

```bash
streamlit run app.py
```

首次启动会自动:
1. 创建 SQLite 数据库 (`data/fab_capacity.db`)
2. 生成 90 天模拟 MES 数据 (约 30~60 秒)
3. 打开浏览器访问 `http://localhost:8501`

---

## 📐 系统架构

```
用户查询 / 定时触发
         ↓
┌──────────────────────────────────────────────┐
│           Orchestrator (编排器)               │
│                                              │
│   ┌────────────┐    ┌────────────┐           │
│   │ Perception │───▶│ Analysis   │           │
│   │   Agent    │    │   Agent    │           │
│   │  感知数据   │    │  分析瓶颈   │           │
│   └────────────┘    └────────────┘           │
│         ↓                  ↓                 │
│   ┌────────────┐    ┌────────────┐           │
│   │ Decision   │───▶│ Execution  │           │
│   │   Agent    │    │   Agent    │           │
│   │  生成决策   │    │  输出报告   │           │
│   └────────────┘    └────────────┘           │
└──────────────────────────────────────────────┘
         ↓
  产能分析报告 + 优化建议 + What-If 对比
```

### PTA 循环

每个 Agent 遵循 **Perceive-Think-Act** 三阶段:

| 阶段 | 说明 |
|------|------|
| **Perceive** | 从数据库/上游 Agent 输出采集数据 |
| **Think** | 调用计算服务/LLM 进行分析决策 |
| **Act** | 结构化输出结果,写回上下文供下游消费 |

---

## 📁 项目结构

```
fab_capacity_agent/
├── app.py                          # Streamlit 主入口 (首页仪表盘)
├── requirements.txt                # Python 依赖
│
├── config/
│   └── settings.yaml               # 全局配置 (DB/产线/Agent/UI)
│
├── data/
│   ├── generator.py                # MES 模拟数据生成器
│   ├── fab_capacity.db             # SQLite 数据库 (自动生成)
│   └── reports/                    # Agent 生成的报告 (自动生成)
│
├── models/
│   ├── database.py                 # DB 管理器 (连接/DDL/CRUD)
│   ├── equipment.py                # 设备 & 事件模型 + DAO
│   ├── wafer.py                    # 批次 & 工序模型 + DAO
│   └── capacity.py                 # 产能快照 + 日产出 DAO + Agent 日志 DAO
│
├── services/
│   ├── capacity_calculator.py      # OEE/UPH/WIP/Snapshot 计算
│   ├── predictor.py                # 产能预测 (MA + LR + LLM)
│   ├── bottleneck_detector.py      # 瓶颈检测 + 根因分析 + 建议
│   └── what_if_simulator.py        # What-If 仿真 + 蒙特卡洛
│
├── agents/
│   ├── base_agent.py               # PTA 基类 (perceive/think/act/run)
│   ├── perception_agent.py         # 感知 Agent: 采集数据构建快照
│   ├── analysis_agent.py           # 分析 Agent: 趋势/瓶颈/异常
│   ├── decision_agent.py           # 决策 Agent: 预测+What-If
│   ├── execution_agent.py          # 执行 Agent: 生成报告
│   └── orchestrator.py             # 编排器: 串联 4 个 Agent
│
├── pages/                          # 5 个 Streamlit 子页面
│   ├── 1_📊_实时监控.py             # 设备状态/WIP/Move 实时看板
│   ├── 2_📈_历史分析.py             # 趋势/异常/瓶颈诊断/Pareto
│   ├── 3_🎯_产能规划.py             # 预测/What-If/蒙特卡洛
│   ├── 4_🤖_Agent工作台.py          # 全链路运行/单Agent调试/报告
│   └── 5_⚙️_系统设置.py             # LLM配置/数据库管理/关于
│
├── tests/
│   └── test_capacity.py            # 单元测试 (23 个用例)
│
└── utils/
    ├── constants.py                # 全局常量 (工序/状态/KPI/颜色)
    ├── helpers.py                  # 通用工具 (配置/日志/格式化/装饰器)
    ├── llm_client.py               # LLM 客户端 (DeepSeek/Qwen)
    └── ui_components.py            # Streamlit 共享 UI 组件
```

---

## 📊 业务覆盖

### 8 道主工序

| 代码 | 中文名 | 设备类型 | 标准工时 (h) |
|------|--------|----------|-------------|
| WET | 清洗 | Wet_Bench | 1.0 |
| PHOTO | 光刻 | Scanner | 2.5 |
| ETCH | 刻蚀 | Etcher | 1.8 |
| DEPO | 沉积 | Deposition | 3.2 |
| IMP | 离子注入 | Implanter | 1.2 |
| DIFF | 扩散 | Furnace | 6.0 |
| CMP | 抛光 | CMP_Tool | 1.5 |
| METRO | 量测 | Metrology | 0.8 |

### 3 种产品

| 产品 | 中文名 | 优先级 | 层数 | 基准良率 |
|------|--------|--------|------|---------|
| Logic_A | 逻辑芯片A | 1 | 12 | 92% |
| Logic_B | 逻辑芯片B | 2 | 10 | 94% |
| Memory_C | 存储芯片C | 3 | 8 | 96% |

### 核心 KPI

| KPI | 说明 | 公式 |
|-----|------|------|
| **OEE** | 综合设备效率 | Availability × Performance × Quality |
| **UPH** | 每小时产出 | 完工片数 / 运行小时 |
| **WIP** | 在制品 | 当前未完工批次晶圆数 |
| **CycleTime** | 周期时间 | end_time - start_time |
| **Throughput** | 吞吐量 | 周期内完工片数 |
| **BottleneckRate** | 瓶颈率 | 瓶颈工序利用率 / 全厂平均 |

### 数据库表 (6 张)

| 表名 | 说明 | 预期行数 |
|------|------|---------|
| equipment | 设备主数据 | 120 |
| lots | 批次信息 | ~5,000 |
| lot_history | 工序历史 | ~70,000 |
| equipment_events | 设备事件 | ~10,000 |
| daily_output | 日产出汇总 | ~90 |
| agent_logs | Agent 执行日志 | 持续增长 |

---

## 🎯 Agent 详解

### 1. PerceptionAgent (感知 Agent)

- **职责**: 从数据库采集近 N 小时数据,构建 `CapacitySnapshot`
- **输入**: `window_hours` (默认 24h)
- **输出**: 全厂/工序级 KPI 快照 (OEE/WIP/UPH/利用率/瓶颈排名)
- **调用服务**: `CapacityCalculator.build_snapshot()`

### 2. AnalysisAgent (分析 Agent)

- **职责**: 趋势分析 + 异常检测 + 瓶颈诊断
- **输入**: Perception 的快照 + 近 N 天历史数据
- **输出**: 瓶颈报告 (瓶颈工序/根因/优化建议)
- **调用服务**: `BottleneckDetector.detect_and_report()`
- **LLM 增强**: 生成自然语言趋势摘要

### 3. DecisionAgent (决策 Agent)

- **职责**: 产能预测 + What-If 情景仿真
- **输入**: Analysis 的瓶颈报告
- **输出**: 7/30 天预测 + 8 种 What-If 情景对比
- **调用服务**: `Predictor.forecast_output()` + `WhatIfSimulator.compare_scenarios()`

### 4. ExecutionAgent (执行 Agent)

- **职责**: 汇总前三步结果,生成 Markdown 产能分析报告
- **输入**: 快照 + 分析报告 + 决策方案
- **输出**: 结构化报告 (执行摘要/KPI/瓶颈/What-If/建议)
- **LLM 增强**: 报告润色
- **持久化**: 报告自动保存到 `data/reports/`

---

## 🧪 测试

```bash
# 方式 1: 直接运行 (推荐, 无外部依赖)
python tests/test_capacity.py

# 方式 2: pytest (需解决 pytest_flask 插件冲突)
python -m pytest tests/test_capacity.py -v -p no:flask
```

测试覆盖 (23 个用例):

| 测试类 | 用例数 | 覆盖范围 |
|--------|--------|---------|
| TestDatabase | 5 | 连接/表结构/行数 |
| TestCapacityCalculator | 5 | OEE/WIP/Snapshot/理论产能/JSON 序列化 |
| TestPredictor | 2 | 单目标/多目标预测 |
| TestBottleneckDetector | 1 | 瓶颈检测报告 |
| TestWhatIfSimulator | 4 | Baseline/预设/对比/自定义情景 |
| TestAgents | 2 | PerceptionAgent 单独/Orchestrator 单 Agent |
| TestOrchestratorPipeline | 1 | 全链路 Pipeline (4 Agent 串联) |
| TestUtils | 3 | safe_div/safe_round/常量 |

---

## ⚙️ 配置说明

`config/settings.yaml` 关键配置项:

```yaml
# 数据库
database:
  path: "data/fab_capacity.db"
  auto_init: true                  # 首次运行自动建库

# 数据生成器
data_generator:
  history_days: 90                 # 历史数据天数
  lots_per_day: 60                 # 日均投料批次
  seed: 42                         # 随机种子 (可复现)

# Agent
agent:
  orchestrator:
    timeout: 300                   # 全链路超时 (秒)
    max_retries: 2                 # 失败重试次数

# What-If 仿真
simulator:
  monte_carlo_iterations: 100      # 蒙特卡洛迭代次数
```

---

## 🔧 常见问题

### Q1: 首次启动很慢?

首次运行需要生成 90 天模拟数据 (约 30~60 秒),后续启动会跳过。如需重建数据,到「系统设置 → 数据库管理 → 数据重建」。

### Q2: LLM 增强有必要开吗?

- **不开**: 本地统计模型已能满足基本预测/分析需求
- **开**: 报告更自然、趋势摘要更智能、瓶颈建议更具体
- 在「Agent 工作台」勾选「启用 LLM 增强」即可

### Q3: 如何调整模拟数据规模?

修改 `config/settings.yaml`:
```yaml
data_generator:
  history_days: 30       # 改为 30 天
  lots_per_day: 30       # 改为 30 批/天
```
然后到「系统设置 → 数据重建」强制重新生成。

### Q4: Streamlit 页面空白?

1. 检查终端是否有 Python 报错
2. 确认数据库已初始化: `python models/database.py`
3. 清除浏览器缓存后刷新

### Q5: pytest 报 pytest_flask 错误?

这是 pytest_flask 插件与新版 Flask 不兼容导致,与本项目无关。解决方式:
```bash
# 方式 1: 禁用 flask 插件
python -m pytest tests/test_capacity.py -v -p no:flask

# 方式 2: 直接运行 (推荐)
python tests/test_capacity.py
```

---

## 🛠 技术栈

| 模块 | 技术 | 版本要求 |
|------|------|---------|
| UI 框架 | Streamlit | ≥ 1.28 |
| 数据处理 | pandas + numpy | ≥ 2.0 / ≥ 1.24 |
| 机器学习 | scikit-learn | ≥ 1.3 |
| 图表可视化 | Plotly | ≥ 5.17 |
| 数据存储 | SQLite (内置) | - |
| 配置管理 | PyYAML + python-dotenv | ≥ 6.0 / ≥ 1.0 |
| LLM 客户端 | requests (调用 OpenAI 兼容 API) | ≥ 2.31 |
| Agent 框架 | 自研 PTA (无外部依赖) | - |

---

## 📜 License

MIT License - 仅供学习和研究使用。

---

## 🤝 贡献

欢迎提 Issue 和 PR 改进系统!

---

*FabCapacityAgent v1.0 · Powered by Streamlit + SQLite + Plotly + PTA Agent Framework*

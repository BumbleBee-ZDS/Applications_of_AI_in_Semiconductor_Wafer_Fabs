# 第27章 动手实验实验室——把关键概念跑起来

## 27.1 为什么需要动手实验

前26章以概念、架构与产业案例为主线，配合的 Demo 脚本（`zh-CN/demos/` 下的 matplotlib 可视化）负责"看一眼就懂"。但要把知识转化为工程能力，还需要第二层：**可以本地运行的完整系统**——有真实的代码结构、可交互的界面、可修改的参数。

本章收录 9 个动手实验，全部来自作者在真实开发中积累并验证过的 MVP 项目，按主题与正文章节的对应关系组织：

| 实验 | 主题 | 对应章节 | 难度 |
| --- | --- | --- | --- |
| 27.3 Ontology 驱动的 Text2SQL | 本体语义层 + 受控 SQL 生成 | 第24/25章、第17章 | ★☆☆ |
| 27.4 晶圆厂 Ontology MVP（RCA Agent） | 本体图 + GraphRAG + ReAct | 第24/25章、第2/14章 | ★★☆ |
| 27.5 FabGraph 双图谱知识平台 | Schema/Lineage 图谱 + NL2SQL | 第14/13/17章 | ★★★ |
| 27.6 K8s 式声明式调度 | 控制论循环 + 多 Agent 调度 | 第7/20章 | ★☆☆ |
| 27.7 产能规划 PTA Agent | 感知-思考-行动 + What-If 仿真 | 第10章 | ★★☆ |
| 27.8 LoRA 微调两阶段查询增强 | 数据合成 + 微调 + 评估 | 第15/17章 | ★★★ |
| 27.9 RTD 实时派工与人机协同 | 分级审批 + 审计追溯 | 第8/11/22章 | ★★☆ |
| 27.10 CIM 可信系统红蓝对抗 | 规则+嵌入+LLM 混合验证 | 第22/23章 | ★★☆ |
| 27.11 多 Agent 评估框架 | 评估质量/成本/韧性 | 第2/21章 | ★☆☆ |

> 所有实验代码位于仓库 `zh-CN/demos/experiments/` 目录（各项目自带 README）。除标注"需 API Key"的实验外，其余均可离线运行；需要 LLM 的实验均提供 Mock/降级模式，无 Key 也能体验核心流程。

## 27.2 实验环境准备

- **Python**：3.10+（FabGraph 与微调实验建议 3.11+）
- **通用依赖**：`pip install -r requirements.txt`（各项目目录内）
- **API Key（可选）**：部分实验使用 DeepSeek/通义千问等大模型，配置 `.env` 文件中的 `API_KEY` 即可启用真实 LLM；未配置时自动降级为规则引擎或 Mock
- **GPU（仅微调实验建议）**：27.8 的 LoRA 训练在 CPU 上可运行（速度较慢），有 NVIDIA GPU 可显著加速

每个实验小节给出"学什么、怎么跑、看什么"三段式说明，建议先跑通再改参数，最后尝试修改一处逻辑观察系统行为的变化——这是理解架构设计意图的最快路径。

## 27.3 实验一：Ontology 驱动的 Text2SQL（fab_ontology_text2sql）

**对应章节**：第24章（Palantir 与本体论）、第25章（Ontology 构建）、第17章（融合概论）

**学什么**：这是理解"为什么 LLM 不能自由写 SQL"的最短路径。实验实现了 Palantir Ontology 思想的三段式 Text2SQL：

- **语义层**：本体字典定义晶圆厂的概念、实体与关系（Lot、Wafer、Equipment、Defect…）
- **动力层**：12 个预定义 SQL 模板，LLM 只负责"选模板 + 填参数"，绝不自由生成 SQL
- **动态层**：SQLite 执行引擎返回结果并渲染图表

这套架构保证了**结果可控、可审计、可解释**——正是第24章所强调的"本体作为受控语义层"的工程体现。

**怎么跑**：

```bash
cd zh-CN/demos/experiments/fab_ontology_text2sql
pip install -r requirements.txt
streamlit run app.py
```

依赖极轻（约 5 个包），离线即可运行；配置 API Key 后切换为 LLM 模式，可对比"规则兜底"与"LLM 选模板"两种路径的输出差异。

**看什么**：在界面输入"W80 批次最近的缺陷记录"这类自然语言，观察系统如何先匹配本体概念、再选择模板、最后生成 SQL——注意全程没有任何自由文本拼接的 SQL。

## 27.4 实验二：晶圆厂 Ontology MVP——本体图驱动的根因分析 Agent（wafer_ontology_mvp）

**对应章节**：第24/25章（Ontology）、第2章（Agent）、第14章（知识图谱）

**学什么**：把第24章"对象-链接-动作"的本体三层映射做成可运行的根因分析（RCA）系统：

- **本体层**：NetworkX + SQLite 构建 Lot/Wafer/Equipment/Defect 实体与关系图，实现 Palantir 三层映射的数据底座
- **推理层**：LangGraph 驱动的 ReAct Agent，通过工具调用在本体图上遍历、检索、归因
- **服务层**：FastAPI 提供本体查询 API，Flask 提供 Web 界面

**怎么跑**：

```bash
cd zh-CN/demos/experiments/wafer_ontology_mvp
pip install fastapi uvicorn sqlmodel networkx langchain langchain-openai langgraph python-dotenv
python src/main.py      # 启动 API 服务（自动播种模拟数据）
python web/app.py       # 启动 Web 界面
```

**看什么**：向 Agent 提问"ETCH-A03 设备相关的批次为什么良率下降"，观察 ReAct 循环如何分解问题、调用本体查询工具、沿"设备→批次→晶圆→缺陷"链路追溯，最后给出带证据链的根因结论。这正是第14章知识图谱辅助 RCA 的完整工程形态。

## 27.5 实验三：FabGraph——双图谱驱动的数据资产平台（FabGraph_MVP）

**对应章节**：第14章（符号主义应用）、第13章（代工服务转型期）、第17章（融合概论）

**学什么**：这是 9 个实验中工程化程度最高的项目，演示晶圆厂数据资产的"元数据治理 + 语义检索"：

- **Schema Graph**：表/字段/类型的结构图谱，支持语义检索与 JOIN 路径推荐
- **Lineage Graph**：数据血缘图谱，回答"这张表从哪来、被谁用"
- **NL2SQL**：基于双图谱上下文的自然语言查询，含社区检测等图算法应用

**怎么跑**：

```bash
cd zh-CN/demos/experiments/FabGraph_MVP
pip install -e ".[dev]"
python scripts/init_mock_data.py
uvicorn fabgraph.main:app --host 0.0.0.0 --port 8000 --reload   # API
streamlit run ui/streamlit_app/app.py                             # 界面
```

无 API Key 时自动降级为 Mock 模式；项目自带 13 个 pytest 测试，可作为"如何为数据平台写测试"的参考。

**看什么**：先浏览 Schema Graph 页面理解元数据组织，再用自然语言提问"刻蚀工序的良率趋势"，观察系统如何借助图谱推荐 JOIN 路径、生成正确 SQL——体会第13章所说的"数据即服务"转型的技术底座。

## 27.6 实验四：K8s 式声明式调度（C9S_agent）

**对应章节**：第7章（制造部/智能调度）、第20章（SA 融合）

**学什么**：把 Kubernetes 的控制论思想（声明式调谐循环）搬进晶圆厂调度：用户声明目标（如"日产出 5000 片"），Supervisor/Scheduler/Worker/Monitor 四个 Agent 通过持续的"期望态-实际态"比对自动调谐，无需人工编写调度脚本。这是第20章"符号+行为"融合（SA）的生动案例：规则系统定义目标与约束，行为系统负责逼近目标。

**怎么跑**：

```bash
cd zh-CN/demos/experiments/C9S_agent
pip install -r requirements.txt   # 仅 2 个依赖
python app.py
```

纯内存模拟，无任何外部依赖，秒级启动。

**看什么**：在仪表盘下发一个产出目标，观察调谐循环如何逐轮缩小偏差；再打开"传统管道对比"页面，对比声明式与命令式两种范式在应对扰动（设备故障注入）时的行为差异。

## 27.7 实验五：产能规划 PTA Agent（FabCapacityAgent）

**对应章节**：第10章（产能爬坡与产能规划）

**学什么**：9 个实验中文档、测试与降级策略最完整的项目，演示"感知（Perception）-思考（Thinking）-行动（Action）"四 Agent 编排的产能分析：

- **实时监控**：OEE、UPH 等指标看板（首次运行自动生成 90 天/120 台设备的模拟 MES 数据）
- **瓶颈检测**：基于排队论与利用率的瓶颈定位
- **What-If 仿真**：蒙特卡洛模拟加机/提速/扩班等方案的产能影响
- **Agent 工作台**：全链路运行或单 Agent 调试，自动生成分析报告

**怎么跑**：

```bash
cd zh-CN/demos/experiments/FabCapacityAgent/fab_capacity_agent
pip install -r requirements.txt
streamlit run app.py
```

首次启动需 30–60 秒生成模拟数据；无 API Key 时 LLM 相关功能自动降级，核心计算功能不受影响。附带 23 个单元测试（`pytest tests/`）。

**看什么**：在 What-If 页面分别模拟"瓶颈设备 +1 台"与"瓶颈工序提速 10%"，对比两者对月产出的影响——直观感受第10章"先找瓶颈、再定投资"的产能规划方法论。

## 27.8 实验六：LoRA 微调——小模型辅助大模型的两阶段查询增强（fab_llm_fine_tuning）

**对应章节**：第15章（连接主义应用）、第17章（融合概论）

**学什么**：微调章节的最佳配套实验，完整走通"数据合成 → LoRA 训练 → 推理 → 量化评估"全链路。核心思路是**两阶段分工**：先用 LoRA 微调 Qwen2-0.5B 小模型做领域查询预处理（补全术语、澄清意图），再交给通用大模型生成最终 SQL——以极低成本获得领域适配能力。

**怎么跑**：

```bash
cd zh-CN/demos/experiments/fab_llm_fine_tuning
pip install -r requirements.txt
python -m fab_mvp.data_generation              # 生成/查看训练数据
python -m fab_mvp.train_lora --smoke --epochs 1   # 冒烟测试（快速验证流程）
python -m fab_mvp.train_lora --epochs 3        # 完整训练
```

仓库已附带训练数据与评估结果（`fab_mvp/outputs/`），不训练也可直接查看评估报告；完整训练需下载 Qwen2-0.5B 基座模型（约 1 GB），CPU 可运行但较慢。

**看什么**：对比 `outputs/eval_summary.json` 中微调前后的指标差异，理解"小模型做预处理"为何能提升端到端准确率——这是第15章"数据稀缺场景下的 AI 加速"主题在 LLM 时代的延伸。

## 27.9 实验七：RTD 实时派工与人机协同（fab_ai_rtd_mvp）

**对应章节**：第8章（制程/设备工程）、第11章（建设期与爬坡期）、第22章（LLM 应用）

**学什么**：唯一完整演示"人工审批 + 审计追溯"的实验，覆盖 RTD（Real-Time Dispatching）派工全链路：

感知（异常检测）→ RAG 诊断（检索历史处置方案）→ 调度建议 → 仿真验证 → **L1–L4 分级人工审批** → 执行与审计日志

分级审批是落地关键：低风险动作自动放行，高风险动作必须人工确认——这正是第11章"建设期人机协同"与第22章"LLM 进厂的信任门槛"两个主题的工程答案。

**怎么跑**：

```bash
cd zh-CN/demos/experiments/fab_ai_rtd_mvp
pip install -r requirements.txt
streamlit run app.py
```

配置 DeepSeek/通义千问 API Key 可启用真实 LLM 诊断；无 Key 时全链路以规则降级运行，审批与审计流程完整可体验。

**看什么**：触发一次设备异常，跟随界面向下走完整条链路，特别注意审批节点——不同风险等级的派工建议会停在不同层级等待人工决策，所有决策留痕可追溯。

## 27.10 实验八：CIM 可信系统红蓝对抗（wafer-trust-guard）

**对应章节**：第22章（LLM 应用）、第23章（Agent 系统）

**学什么**：用"红蓝对抗"的对抗式演练回答"如何验证 AI 系统可信"：

- **红队**：生成试图绕过管控的违规 Recipe（模拟攻击与误用）
- **蓝队**：四层验证防线——静态规则校验 → Embedding 语义对齐 → LLM Judge 评审 → FA 记忆闭环（历史案例召回）

四层防线恰好对应第18章神经符号思想的"规则 + 向量 + 大模型"混合验证，是治理与信任主题的稀缺配套实验。

**怎么跑**：

```bash
cd zh-CN/demos/experiments/wafer-trust-guard
pip install -r requirements.txt
streamlit run app.py
```

全链路带 Mock 兜底，无 Key 可完整运行。

**看什么**：观察同一违规 Recipe 在四层防线中的拦截位置——有的被静态规则直接拦下，有的穿透到 LLM Judge 才被识别。思考：如果只保留其中一层，系统会在哪里失守？

## 27.11 实验九：多 Agent 评估框架（fab_agent_test）

**对应章节**：第2章（AI 简史/Agent 概念）、第21章（NSA 全融合）

**学什么**：回答"怎么评估一个 Agent 系统好不好"。手写 Planner/ToolSet/Reflector/Orchestrator 四模块协作完成缺陷 RCA，同时**实时评估**三类指标：

- **过程质量**：任务分解合理性、工具调用正确率
- **资源成本**：调用轮次、时延
- **系统韧性**：注入 30% 超时故障，观察系统能否恢复并完成任务

零外部 AI 依赖（纯 Mock），白盒实现，是理解 Agent 评估方法论的最佳起点。

**怎么跑**：

```bash
cd zh-CN/demos/experiments/fab_agent_test
pip install streamlit
streamlit run app.py
```

**看什么**：运行一次完整评估，重点看韧性测试段——当工具调用超时时，Orchestrator 的重试与降级策略如何生效，评估指标如何实时反映系统状态。

## 27.12 从实验到生产：改造指引

本章实验均为 MVP 形态，走向生产环境通常还需要以下改造（各实验的完整设计文档见其目录内 README）：

1. **数据接入**：把模拟数据生成器替换为 MES/EAP/SPC 真实数据接口，注意保持本体/图谱 Schema 稳定
2. **密钥管理**：将 `.env` 中的 API Key 迁移至企业密钥管理系统，按最小权限分配
3. **评估闭环**：参考 27.11 的三维评估框架，为每个上线的 Agent 建立持续评估
4. **审批与审计**：涉及生产动作的系统，照搬 27.9 的分级审批与审计日志设计
5. **信任验证**：对外提供决策建议的系统，用 27.10 的红蓝对抗思路做上线前演练

> 实验是理解的捷径，也是质疑的起点。跑通之后，不妨问自己：如果晶圆厂的真实数据分布与模拟数据不同，这个系统的哪个环节会最先失效？——这正是从 Demo 走向落地的第一道门槛。

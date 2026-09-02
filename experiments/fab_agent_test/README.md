# 🔬 半导体晶圆厂（FAB）多 Agent 评估框架 MVP

> 模拟"晶圆缺陷根因分析"的多 Agent 协作流程，并实时展示
> **过程质量 / 资源成本 / 系统韧性** 三类评估指标。
>
> 纯 Python 手写 Agent 逻辑，无 LangChain / CrewAI 依赖，可直接 `streamlit run app.py` 运行。

---

## 目录

1. [项目概览](#项目概览)
2. [目录结构](#目录结构)
3. [技术约束](#技术约束)
4. [业务场景](#业务场景)
5. [Agent 架构（白盒模块）](#agent-架构白盒模块)
6. [执行流程](#执行流程)
7. [评估器（核心）](#评估器核心)
8. [Streamlit UI 布局](#streamlit-ui-布局)
9. [安装与运行](#安装与运行)
10. [生成更多测试数据（DeepSeek）](#生成更多测试数据deepseek)
11. [示例运行结果](#示例运行结果)
12. [扩展点](#扩展点)
13. [FAQ](#faq)

---

## 项目概览

本项目是一个最小可运行 Demo（MVP），面向半导体晶圆厂（FAB）的
"缺陷根因分析"业务场景，演示了一个多 Agent 协作系统的典型流程：

```
用户问题  →  Planner(拆解子任务)
          →  ToolSet(查批次 / 查机台 / 查配方 / 查历史)
          →  Reflector(检查数据矛盾)
          →  Orchestrator(主循环 + 失败自愈)
          →  最终根因报告 + 建议
```

同时，评估器 `Evaluator` 在 Agent 运行期间实时收集：

| 维度 | 指标 |
|---|---|
| **过程质量** | 已执行步数（上限 6）、Reflector 是否发现数据矛盾 |
| **资源成本** | 工具调用总次数、模拟 Token 消耗（1 字符 = 1 token） |
| **系统韧性** | 重试次数、是否死循环、是否优雅处理超时（韧性评分） |
| **业务价值** | 最终结论是否包含可执行"建议" |

---

## 目录结构

```
fab_agent_test/
├── app.py                       # Streamlit UI 入口（仅 UI 层，不含业务逻辑）
│
├── core/                        # 🧠 Agent 核心模块（白盒）
│   ├── __init__.py              # 对外统一导出 API
│   ├── evaluator.py             # Evaluator：评估指标收集（三大维度）
│   ├── memory.py                # Memory：键值对记忆（保存 Lot ID 等）
│   ├── toolset.py               # ToolSet：4 个工具（含 30% 超时接口）
│   ├── planner.py               # Planner：生成/调整执行计划
│   ├── reflector.py             # Reflector：检查 recipe vs 机台日志 矛盾
│   └── orchestrator.py          # Orchestrator：主循环（步数上限 + 死循环检测）
│
├── data/                        # 📦 Mock 数据层
│   └── mock_data.py             # LOT_DB / RECIPE_DB / 生成数据加载逻辑
│
├── gen_test_data.py             # 🤖 调用 DeepSeek 生成测试数据与问题
├── fab_test_data.json           # （可选）DeepSeek 生成的 8 批次 + 6 问题
│
├── .env                         # API 配置（DEEPSEEK / DASHSCOPE）
└── README.md                    # 本文件
```

解耦后各层依赖关系：

```
app.py ──▶ core / evaluator / memory / toolset / planner / reflector / orchestrator
  │           ▲            ▲
  │           │            │
  │           │            └──▶ data / mock_data.py  (LOT_DB / RECIPE_DB)
  │           └──────────────────────┘
  └──▶ fab_test_data.json ◀── gen_test_data.py ◀── .env (DEEPSEEK_API_KEY)
```

---

## 技术约束

✅ 本项目严格遵守以下约束：

| 约束项 | 要求 | 实际实现 |
|---|---|---|
| Python 版本 | 3.10+ | 3.10+ 语法（f-string、dict 增强、list[str] 等） |
| 允许依赖 | `streamlit, dataclasses, random, time, typing, json` | ✅ 仅标准库 + streamlit |
| Agent 框架 | **禁止** LangChain / CrewAI 等 | ✅ 全部手写 `core/` 模块 |
| 数据源 | **不连真实 DB**，全部 Mock | ✅ `data/mock_data.py` 硬编码 + `fab_test_data.json` |
| 不稳定接口模拟 | Equipment API 30% 超时 | ✅ `ToolSet._call_equipment_api()` 用 `random` 模拟 |
| LLM 调用 | 报告用 f-string 生成，不调真实 LLM | ✅ `Orchestrator._generate_report()` |

> 说明：`.env` 中的 DeepSeek / DashScope API Key **仅用于**
> `gen_test_data.py` 批量生成更丰富的测试数据（可选），
> Agent 运行阶段不需要任何 API Key。

---

## 业务场景

**用户角色**：工艺工程师

**输入示例**（可在 UI 中输入或选择）：

1. `批次 W12345 的关键尺寸（CD）超标，分析原因。`
2. `批次 W12346 的 CD 偏小，请排查可能的影响因素。`
3. `批次 W12350 与 W12351 在 ETCH-CH-007 连续出现 CD 超标，是否存在关联性？`

**系统需依次完成**：

```
查批次信息 → 查对应机台(Etch Chamber)运行日志 → 查最近工艺配方(Recipe)
→ Reflector 检测矛盾 → 给出结论 + 建议
```

若机台接口超时（30% 概率）：重试 1 次 → 仍失败 →
**Planner 自动调整计划**（降级为批次历史推断），实现"失败自愈策略"。

---

## Agent 架构（白盒模块）

### 1. Memory（记忆模块）
核心能力：保存批次号（Lot ID），防止 Agent 在多步执行中遗忘。
```python
m = Memory()
m.store("lot_id", "W12345")
m.recall("lot_id")   # → "W12345"
```
- 后续扩展方向：持久化 JSON 存储 / 向量长期记忆 / Sliding Window。

### 2. ToolSet（工具集）
4 个 Mock 工具，统一由 Evaluator 记录 `tool_call_count` 与死循环签名：

| 工具 | 稳定性 | 说明 |
|---|---|---|
| `get_lot_info(lot_id)` | ✅ 稳定 | 返回产品、CD 目标/实测、腔体、状态 |
| `get_equipment_log(chamber_id)` | ⚠ 30% 超时 | 返回压力/RF功率/温度；**自动重试 1 次** |
| `get_recipe_params(lot_id)` | ✅ 稳定 | 返回 recipe_id、设定压力、工艺时间 |
| `get_lot_history(lot_id)` | ✅ 稳定 | **降级工具**，设备接口不可用时替代 |

### 3. Planner（规划器）
- `make_plan(question)` → 返回 5 步标准计划；
- `adjust_plan_skip_equipment(plan)` → 失败自愈：把"机台日志"步骤替换为"批次历史推断（降级）"，仅允许调整 1 次。

### 4. Reflector（反思器）
检查工具返回数据的**一致性**：

```
recipe.pressure_setpoint  (5.0 mTorr，正常)
      ↕  |差值| > 1.0 → 冲突！
equipment_log.pressure    (6.8~7.6 mTorr，异常)
```

发现矛盾时标记 `Evaluator.reflection_valid = True`。

### 5. Orchestrator（编排器 / 主循环）
按步骤依次调度，内置双重终止保护：

```python
while idx < len(plan):
    if step_count >= max_steps:           # ① 步数上限 6
        break
    if evaluator.dead_loop_flag:          # ② 连续 2 步同工具同参数
        break
    # 分发到步骤 → 调用 ToolSet / Reflector
```

报告生成：`_generate_report()` 用 f-string 拼接，**动态取腔体号和 CD 偏差方向**（避免硬编码 ETCH-CH-007）。

### 6. Evaluator（评估器）
详见下一节。

---

## 执行流程

```
用户点击 [🚀 开始分析]
    │
    ├─ Memory.store(lot_id)
    │
    ├─ Planner.make_plan()
    │   → ["查询批次信息", "查询机台运行日志", "查询工艺配方", "反思", "报告"]
    │
    ├─ Orchestrator.run()
    │   ├── Step 1  get_lot_info(W12345)     → CD 超标
    │   ├── Step 2  get_equipment_log(ETCH-CH-007)
    │   │         └─ 30% 超时 → 重试 → 仍失败 →
    │   │            Planner.adjust_plan_skip_equipment()
    │   │            Step 2 被替换为：get_lot_history()（降级）
    │   ├── Step 3  get_recipe_params(W12345) → 配方设定压力 5.0
    │   ├── Step 4  Reflector.check_conflict()
    │   │         └─ 配方 5.0 vs 机台 7.1 → 矛盾 detected!
    │   └── Step 5  _generate_report()  → 根因 + 3 条建议
    │
    └─ 左侧：日志 + 报告；右侧：实时指标卡片
```

---

## 评估器（核心）

### 指标清单

| 指标 | 说明 | 对应原则 |
|---|---|---|
| `step_count` | 已执行步数（上限 6） | 过程质量 |
| `reflection_valid` | Reflector 是否发现矛盾 | 过程质量 |
| `tool_call_count` | 工具调用总次数 | 资源成本 |
| `token_cost_mock` | 1 字符 = 1 token，全部输出累加 | 资源成本 |
| `retry_count` | 工具超时后重试次数 | 系统韧性 |
| `dead_loop_flag` | 连续 2 步同工具同参数则 True | 系统韧性 |
| `timeout_handled` | 重试后是否恢复（决定韧性评分） | 系统韧性 |
| `resilience_score()` | 高(未触发)/高(已自愈)/中(未恢复) | 系统韧性 |
| `business_value()` | 最终报告是否含"建议" | 业务价值 |

### 死循环检测机制

每次工具调用生成签名：
```
"name|args_json_sorted"
```
若连续 2 次签名完全相同 → `dead_loop_flag = True`，Orchestrator 强制 break。

### 韧性评分规则

| 场景 | 评分 |
|---|---|
| `retry_count == 0` | **高**（未触发超时） |
| `retry_count > 0 && timeout_handled` | **高**（已自愈） |
| 其他（重试仍失败，降级） | **中**（已重试但未恢复） |

---

## Streamlit UI 布局

两栏布局（`st.columns([3, 2])`）：

### 左侧：🛠 输入与执行流
- **示例问题下拉框**：DeepSeek 生成的 6 条问题，选择后自动填充到输入框；
- **工艺工程师问题 text_input**：手动输入或编辑；
- **🚀 开始分析 button**：启动 Orchestrator；
- **执行日志 code 区**：实时追加显示
  `[Planner] / [Tool] / [Reflect] / [Step N] / [Memory]` 等标记；
- **📄 最终报告 markdown**：流程结束后展示根因与建议。

### 右侧：📊 评估面板
- `st.metric` 4 张卡片：执行步数 / 工具调用次数 / 模拟 Token 消耗 / 重试次数；
- `st.success` / `st.error`：死循环检测状态；
- **韧性评分**：高亮文本；
- `st.warning` / `st.info`：反思有效性；
- `st.success` / `st.error`：业务价值（是否含建议）；
- `st.expander`：`evaluator.to_dict()` 完整 JSON。

---

## 安装与运行

### 1. 依赖安装

```bash
pip install streamlit>=1.57
```

> 本项目仅依赖 `streamlit`，其余均为 Python 标准库。

### 2. 启动

```bash
cd fab_agent_test
python -m streamlit run app.py
```

浏览器会自动打开 http://localhost:8501

### 3. 最小测试

输入框使用默认值 `批次 W12345 的关键尺寸（CD）超标，分析原因。`，
点击「开始分析」即可。

反复点击「开始分析」约 **每 3 次** 会触发一次
"设备接口超时 → 重试 → 降级自愈"的韧性场景，可观察右侧 `重试次数`
与 `韧性评分` 的变化。

---

## 生成更多测试数据（DeepSeek）

项目内置了 `gen_test_data.py` 脚本，利用 `.env` 中的
`DEEPSEEK_API_KEY` 调用 `deepseek-chat` 模型批量生成：

- 8 个批次（CD超标 / CD偏小 / 厚度异常 / 正常 / 同腔体关联 共 5 类场景）
- 8 条工艺配方（每批对应 1 个，配方设定值正常以制造冲突）
- 6 条自然语言问题（覆盖单批次分析、关联性、对比分析）

### 用法

```bash
python gen_test_data.py
```

输出文件：`fab_test_data.json`（下次启动 `app.py` 时会被**自动合并**到
`LOT_DB` / `RECIPE_DB`，优先覆盖同名批次）。

### 脚本说明

| 项 | 说明 |
|---|---|
| API 来源 | 读取 `.env` 中 `DEEPSEEK_API_KEY` + `DEEPSEEK_BASE_URL` |
| 请求库 | 仅使用标准库 `urllib.request`（无需 `requests`） |
| 输出格式 | 强制 `response_format: json_object`，脚本做二次归一化 |
| 字段校验 | `normalize_lot` / `normalize_recipe` 补齐缺失字段 |

---

## 示例运行结果

### ✅ 场景 A：常规路径（未触发超时）
```
批次 W12345 → CD超标 52.8nm / 目标 50.0nm
机台 ETCH-CH-007 压力 6.83mTorr vs 配方设定 5.0mTorr
Reflector → ⚡ 发现压力数据矛盾
最终报告 → 3 条建议
评估：步数 5/6、工具 3 次、Token ~970、韧性=高（未触发超时）
```

### ⚠ 场景 B：超时自愈全链路（W12346 CD偏小）
```
批次 W12346 → CD偏小 44.1nm / 目标 45.0nm
get_equipment_log(ETCH-CH-012) 超时（30% 概率命中）
  → 重试 1 次 → 仍失败
  → Planner.adjust_plan_skip_equipment()
  → 步骤替换为：get_lot_history（降级）
最终报告 → "根因结论（基于历史推断）" + 2 条建议
评估：步数 6/6、工具 4 次、重试 1 次、韧性=中（已重试但未恢复）
```

### 📊 评估面板 JSON 明细示例
```json
{
  "step_count": 6,
  "tool_call_count": 4,
  "token_cost_mock": 912,
  "retry_count": 1,
  "dead_loop_flag": false,
  "reflection_valid": false,
  "timeout_handled": false,
  "resilience_score": "中（已重试但未恢复）",
  "business_value": true
}
```

---

## 扩展点

### 1. 接入真实 LLM（替换报告生成）
在 `core/orchestrator.py` 的 `_generate_report()` 中，
把当前 f-string 拼接改为调用 DeepSeek / 通义千问：
```python
# 读取 .env → urllib.request POST 到 DEEPSEEK_BASE_URL/chat/completions
# 返回值填入 report
```
同时可把 `Planner.make_plan()` / `Reflector.check_conflict()`
改为 LLM 驱动，保留相同返回结构即可。

### 2. 替换 Mock 为真实接口
`data/mock_data.py` 中 `LOT_DB` / `RECIPE_DB` 改为从 MES / DB 查询；
`core/toolset.py` 的 `_call_equipment_api()` 改为真实 REST / SECS/GEM 调用，
保留超时返回 `None` 的协议即可。

### 3. 增加更多 Agent
在 `core/` 下新增 `reporter.py`（总结报告 Agent）、`validator.py`
（建议可执行性审核）等模块，在 `Orchestrator.run()` 的步骤分发中添加即可。

### 4. 长期评估日志
在 `Evaluator.to_dict()` 结束时追加写入 `runs/yyyyMMdd_HHMMSS.json`，
便于后续批量统计（A/B 对比不同 Planner 策略）。

### 5. DashScope Embedding（`.env` 中已有）
`QWEN_EMBEDDING_MODEL=qwen3.7-text-embedding` 可用于：
- 历史批次特征向量化 + 相似度检索（替代当前纯字符串匹配）；
- 问题聚类（按缺陷类型分组）。

---

## FAQ

**Q1：为什么不使用 LangChain / CrewAI？**
A1：MVP 技术约束要求"所有 Agent 逻辑手写"，便于白盒观察每个模块的
独立行为与评估指标；`core/` 中 6 个类总代码量仅 ≈ 600 行，无依赖负担。

**Q2：`gen_test_data.py` 失败或超时怎么办？**
A2：`fab_test_data.json` 是**可选**的——即使它不存在，
`app.py` 也会用内置 2 条批次（W12345 / W67890）正常演示。
如遇 API Error，可检查 `.env` 中 `DEEPSEEK_API_KEY` 是否正确。

**Q3：为什么有时候"超时自愈"没出现？**
A3：超时是 30% 概率（`EQUIP_TIMEOUT_RATE = 0.30`），
约每 3 次运行触发 1 次；可在 `data/mock_data.py` 中临时改大到
`1.0` 即可 100% 复现超时自愈场景。

**Q4：死循环检测"连续 2 步同工具同参数"会不会误伤？**
A4：Planner 的 `make_plan()` 每次生成 5 步各不相同的步骤，
只有在 bug 导致 Orchestrator 反复调用同一工具时才触发；
可把步数上限调到 `max_steps = 6` 做双重保险。

**Q5：如何验证报告是否"有业务价值"？**
A5：`Evaluator.business_value()` 目前用简单规则
`"建议" in final_report` 判定。后续可改为：检查建议列表长度 ≥ 2 条、
或调用 LLM 做分类评分（同样可在 Evaluator 中新增字段）。

---

## License

MIT

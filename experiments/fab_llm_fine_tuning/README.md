# 🔬 晶圆厂 LLM 两阶段查询增强 MVP

> 用微调的 **小模型 (0.5B)** 做领域查询预处理，为 **强模型 (DeepSeek)** 注入晶圆厂结构化上下文，生成更精准的 SQL 与分析回答。

## 核心思路

晶圆厂工程师常以口语/黑话提问（"3号机良率掉的厉害咋回事"），直接丢给强模型会因缺乏领域知识（表名、缩写、SOP）而生成泛化、不精准的 SQL。

本项目用 **两阶段架构** 解决：

```
用户口语问题
    │
    ▼
┌──────────────────────────────┐
│  Stage 1: 微调小模型 (0.5B)   │  ← LoRA 微调 Qwen2-0.5B
│  预处理为结构化 JSON          │
│  (intent/entities/hints/SQL)  │
└──────────┬───────────────────┘
           │ 结构化上下文
           ▼
┌──────────────────────────────┐
│  Stage 2: 强模型 (DeepSeek)   │  ← 拿到上下文后生成精准 SQL
│  生成最终 SQL / 分析回答      │
└──────────────────────────────┘
```

**三种预处理模式**（一个微调模型支持）：

| 模式 | 功能 | 输出示例 |
|------|------|---------|
| `mode_a` 领域感知增强 | 提取意图/实体/领域提示/增强查询 | `{"intent":"yield_analysis", "entities":{"eqp_id":"EQP-003"}, ...}` |
| `mode_b` 术语翻译 | 口语/黑话 → 专业术语表述 | `{"translated":"查询设备EQP-003的CP良率..."}` |
| `mode_c` SQL模板路由 | 匹配知识库中的SQL模板 | `{"template_id":"SQL_TMPL_YIELD_01", "params":{...}}` |

## 项目结构

```
fab_llm_fine_tuning/
├── Qwen2-0.5B/                  # 基座模型 (HuggingFace 下载)
├── .env                         # DEEPSEEK_API_KEY
├── requirements.txt
├── fab_mvp/
│   ├── knowledge_base.py        # 晶圆厂知识库 (7表/35缩写/8 SQL模板/5 SOP)
│   ├── data_generation.py       # 用 DeepSeek 合成训练数据
│   ├── train_lora.py            # LoRA 微调 (一模型三模式混合训练)
│   ├── inference.py             # 小模型推理 (懒加载, robust JSON解析)
│   ├── agent.py                 # LangGraph 编排 (增强路径 vs 直接路径)
│   ├── app.py                   # Streamlit UI
│   ├── eval_cases.py            # 10 条评估用例
│   ├── eval_runner.py           # 评估实验脚本 (自动化指标对比)
│   ├── data/
│   │   ├── train.jsonl          # 120 条训练数据 (三模式标注)
│   │   └── eval.jsonl           # 30 条评估数据
│   └── outputs/
│       └── lora_adapter/        # 微调后的 LoRA adapter
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目后，创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=sk-your-api-key-here
```

### 3. 下载基座模型

将 Qwen2-0.5B 模型下载到项目根目录的 `Qwen2-0.5B/` 文件夹：

```bash
# 方式一: huggingface-cli
huggingface-cli download Qwen/Qwen2-0.5B --local-dir Qwen2-0.5B

# 方式二: git lfs
git lfs install
git clone https://huggingface.co/Qwen/Qwen2-0.5B
```

### 4. 合成训练数据（可选，已有数据可跳过）

```bash
python -m fab_mvp.data_generation
# 生成 fab_mvp/data/train.jsonl (120条) 和 eval.jsonl (30条)
```

### 5. LoRA 微调

```bash
# 全量训练 (120样本×3模式=360条, 3 epochs)
python -m fab_mvp.train_lora --epochs 3

# 快速验证 (9条, 1 epoch)
python -m fab_mvp.train_lora --smoke --epochs 1

# 限制样本数 (如只用60条原始样本)
python -m fab_mvp.train_lora --limit 60 --epochs 3
```

**微调参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--epochs` | 3.0 | 训练轮数 |
| `--lr` | 2e-4 | 学习率 |
| `--batch` | 4 | 每设备批大小 |
| `--grad-accum` | 4 | 梯度累积步数 |
| `--lora-r` | 16 | LoRA 秩 |
| `--smoke` | - | smoke 测试 (仅9条) |
| `--limit` | 0 | 限制原始样本数 |

> **CPU 训练提示**：0.5B + LoRA 可在 CPU 上运行，但较慢（约 4-5 分钟/步）。建议至少训练 2-3 个 epoch 让模型学会 JSON 输出格式。

### 6. 推理验证

```bash
python -m fab_mvp.inference
# 用测试问题跑三种模式，打印 JSON 输出
```

### 7. Agent 对比验证

```bash
python -m fab_mvp.agent "昨天3号机良率掉的厉害咋回事"
# 同时跑增强路径和直接路径，对比输出
```

### 8. 启动 Web UI

```bash
python -m streamlit run fab_mvp/app.py
# 浏览器访问 http://localhost:8501
```

### 9. 评估实验

```bash
# 10 用例 × 2 路径对比 (用标准JSON模拟理想小模型, 隔离小模型质量问题)
python -m fab_mvp.eval_runner --n 10 --mode mode_a
```

## 知识库

[knowledge_base.py](fab_mvp/knowledge_base.py) 模拟晶圆厂领域知识，包含四部分：

| 模块 | 内容 | 数量 |
|------|------|------|
| `FAB_SCHEMA` | 表结构 + 字段解密 | 7 张表 |
| `GLOSSARY` | 缩写词典 (CP/FT/WAT/SPC/OOC/PM...) | 35 条 |
| `SQL_TEMPLATES` | 分析 SQL 模板库 | 8 个模板 |
| `SOP_SNIPPETS` | SOP 流程片段 | 5 条 |

**7 张表**：`WIP_LOT`(在制品批次)、`EQUIPMENT`(设备主数据)、`PROCESS_LOG`(工艺日志)、`YIELD_SUMMARY`(良率汇总)、`DEFECT_DATA`(缺陷坐标)、`OOC_ALARM`(SPC告警)、`RECIPE`(配方)

**8 个 SQL 模板**：良率异常查询、设备关联批次、缺陷热点分析、批次追溯、SPC告警查询、PM前后对比、工艺参数偏离、Hold批次查询

## 评估结果

用 `eval_runner.py` 对 10 条测试用例进行对比实验（用标准 JSON 模拟理想小模型输出，隔离小模型质量问题）：

| 指标 | 增强路径 | 直接路径 | 差值 | 增强胜 |
|------|---------|---------|------|--------|
| **知识库表名引用数** | 2.60 | 0.40 | +2.20 | 9/10 |
| **实体命中率** | 86% | 54% | +32% | 7/10 |
| 模板正确率 | 10% | 0% | +10% | - |

**结论**：结构化上下文让强模型从"广撒网式猜测"变为"精准引用知识库表名与实体"。增强路径在知识库表名引用上 9/10 胜出，实体命中率提升 32 个百分点。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 基座模型 | Qwen2-0.5B | 0.5B 参数, CPU 可跑 |
| 微调方法 | LoRA (PEFT) | r=16, target=q/k/v/o_proj |
| 训练框架 | TRL SFTTrainer | 指令微调, packing=False |
| 强模型 | DeepSeek Chat | 通过 OpenAI 兼容 API 调用 |
| 编排框架 | LangGraph | StateGraph 双路径并行 |
| Web UI | Streamlit | 增强路径 vs 直接路径并排展示 |
| 数据合成 | DeepSeek | 基于知识库批量生成训练数据 |

## 架构亮点

1. **小模型做大模型做不好的事**：0.5B 小模型不负责推理，只负责"窄而深"的领域信号放大（缩写解密、表名映射、模板路由），把推理留给强模型
2. **一模型三模式**：通过指令前缀区分模式，一个 LoRA adapter 支持三种预处理，无需三个模型
3. **训练/推理格式一致**：`SYSTEM_PROMPT` + `MODE_PROMPTS` 在训练和推理时共用，保证微调生效
4. **双路径对比**：LangGraph 同时跑增强路径和直接路径，直观展示小模型预处理的增量价值

# 🛡️ wafer-trust-guard —— CIM 可信系统工程「红蓝对抗」MVP Demo

> **工艺配方（Recipe）就是芯片设计代码。**
> 红队 Agent 负责『偷工减料』，蓝队 Verifier 拥有绝对否决权与『历史记忆』。
> 核心信念：**Design is cheap, Verification is everything.**
>
> 本系统模拟了台积电/中芯国际的 Tape-out 验证与 FA 闭环流程。

## 快速开始

```bash
# 1. 配置 .env（无需改代码，Key 一律从环境读取）：
#    DEEPSEEK_API_KEY=sk-xxx          # DeepSeek（OpenAI SDK 兼容）
#    DASHSCOPE_API_KEY=sk-xxx         # 阿里云 DashScope（千问 qwen3.7-text-embedding）
# 2. 安装依赖
pip install -r requirements.txt
# 3. 启动（首次运行自动生成 failure_log.json 知识库）
streamlit run app.py
```

## 红蓝对抗 + FA 闭环流程

1. **顶部选择对抗模式**：`正常 Agent（mock）` vs `红队攻击模式（DeepSeek）`；
2. **左侧**输入工艺需求（红队模式建议『做高温扩散，要安全』）；
3. **中间**点击「生成 Recipe」：红队模式由 DeepSeek 扮演『急于下班的工艺工程师』，生成**表面合规、暗藏违规**的 Recipe；
4. **右侧**蓝队 Verifier 层层把关：
   - **📚 历史失效库匹配**：先查 FA 知识库，命中相似历史立刻告警（⚠️ 检测到 N 条相似工艺曾在历史中被拦截）；
   - **L1 静态门禁**：温度物理极限、气体白名单、Pydantic 字段类型；
   - **Embedding 意图对齐**：千问 `qwen3.7-text-embedding` 余弦相似度，< 0.7 判『意图偏离』（`st.progress` 显示对齐分）；
   - **LLM-as-Judge**：DeepSeek 扮演资深 PE，注入历史案例 Few-Shot，reason 标注是否『命中历史失效模式』；
   - **最终裁决**：`🟢 允许下发机台` / `🔴 拦截（防止晶圆报废）`；
5. **FA 闭环**：每次被拦截的违规自动写入 `failure_log.json`（FA-编号入库，加入工艺黑名单），下次遇到类似需求立刻触发历史告警 —— **Verifier 拥有『记忆』**。

## 目录结构

```
wafer-trust-guard/
├── app.py                        # Streamlit 入口（红蓝对抗 + FA 记忆 UI）
├── config.py                     # .env 加载 + DeepSeek 客户端（OpenAI SDK 兼容）
├── failure/                      # 失效分析知识库（FA 记忆）
│   ├── __init__.py
│   ├── embedder.py               # 千问 qwen3.7-text-embedding 封装（失败返回零向量）
│   └── fa_store.py               # FA 案例存/查（本地 JSON + 余弦检索，无 Chroma/FAISS）
├── generator/
│   ├── __init__.py
│   ├── mock_agent.py             # 正常模式：80% 合规 / 20% 幻觉（纯本地）
│   └── redteam_agent.py          # 红队模式：DeepSeek 生成暗藏违规的 Recipe（失败本地兜底）
├── verifier/
│   ├── __init__.py               # Verdict 结果类型
│   ├── static_rules.py           # L1 静态门禁（物理极限、白名单、Pydantic 类型）
│   ├── alignment_embedding.py    # L2 Embedding 意图对齐（qwen3.7-text-embedding + 余弦相似度）
│   ├── llm_judge.py              # L3 LLM-as-Judge（DeepSeek + 历史 FA Few-Shot）
│   ├── alignment.py              # （保留）规则版意图对齐
│   └── invariants.py             # （保留）属性不变量
├── schemas/
│   ├── __init__.py
│   └── recipe.py                 # Pydantic Recipe 数据契约
├── failure_log.json              # 自动生成的本地 FA 知识库（已 gitignore）
├── requirements.txt
└── README.md
```

## 失效分析知识库（FA 记忆）设计

- **存储**：本地 `failure_log.json`（JSON 文件存向量，MVP 不引入 Chroma/FAISS，数据不丢）；
- **向量化**：`failure/embedder.py` 用千问 `qwen3.7-text-embedding`，失败返回零向量不报错；
- **入库**：`fa_store.add_case(req, recipe, reason, layer)`，文本 = `需求：{req}。违规原因：{reason}`；
- **检索**：`fa_store.search(req, top_k=3)` 余弦相似度 ≥ 0.6 视为『相似历史』；
- **Few-Shot**：`llm_judge.py` 把历史案例注入 System Prompt，提醒资深 PE『上次这么干炸过』；
- **首次运行自动播种** 3 条模拟 FA 档案（高温扩散超温 / 清洗用错气体 / 刻蚀时长过短）。

## 设计说明

- **绝对不写死 API Key**：统一从 `.env` 经 `config.py` 读取；
- **所有 LLM 调用均 try/except + mock 兜底**：DeepSeek / DashScope 任一不可用，Demo 自动降级为本地规则，绝不崩溃；
- **物理隔离**：Generator（含红队）不 import 任何 verifier / failure 代码 —— **设计不知道验证的历史**；
- **UI 约束**：仅 Streamlit 原生组件（`st.json` / `st.progress` / `st.expander` / `st.success` / `st.error`），无自定义 CSS/HTML；
- 红队模块仅用于演示与验证层压力测试，不用于任何真实生产环境。

## 免责声明

本项目为教学演示 MVP：红队行为为模拟设定，验证规则与 FA 数据为示例；真实 CIM 系统需结合设备手册、工艺工程规范与仿真数据。
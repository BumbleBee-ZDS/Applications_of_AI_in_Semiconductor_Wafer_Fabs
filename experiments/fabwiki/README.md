# FabWiki — 半导体晶圆厂数据资产知识库与 Text2SQL MVP
# FabWiki — Semiconductor Fab Data Asset Knowledge Base & Text2SQL MVP

[English](#english) · [中文](#中文)

---

<!-- tabs:start -->

## 中文

大型晶圆厂（Fab）的 Oracle 数仓中，MES / EAP / YMS 表结构复杂、字段编码含义晦涩、
存储过程逻辑充满**隐性知识**（例如 `LOT_STS='05'` 表示 *Hold 待 MRB 评审*）。
这类知识不在数据字典里，只存在于老工程师的脑子里——朴素 Text2SQL 直接查询
准确率极低。

**FabWiki** 基于 **OKF（Open Knowledge Format）** 思想，把
「数据字典 + 隐性知识 + Text2SQL 注意事项」编译成一张**可导航的知识图谱**，
让 LLM **确定性读取** 而非「向量分块检索」所需知识后再生成 SQL。

这是最小可运行 MVP：**离线（无 API Key）也能完整演示**。

- ✅ 8 张 Fab 风格表 + 2 个指标，含 5 类「隐性知识」陷阱
- ✅ 4 个 Streamlit 页面：首页 / 知识浏览 / 血缘图谱 / Text2SQL
- ✅ Mock / 真实 LLM 双模式，无缝切换
- ✅ 知识导航式 Text2SQL：定位 → 确定读全文 → 生成 → 执行 → 失败重试

---

### 1. 背景：为什么朴素 Text2SQL 在 Fab 里会「翻车」

Text2SQL 难的不是「写 SQL」，而是「让模型懂业务语义」。Fab 数仓里有典型的
**隐性知识陷阱**：

| 陷阱 | 错误 SQL | 正确 SQL |
|------|----------|----------|
| **魔法编码**：`LOT_STS`，`05`=Hold、**`99`=测试批次** | `WHERE LOT_STS='05'` | `WHERE LOT_STS='05' AND LOT_STS<>'99'` |
| **前缀编码**：`DEFECT_CD`，`P*`=Particle… | `WHERE DEFECT_CD='P12'` | `WHERE DEFECT_CD LIKE 'P%'` |
| **字段类型**：`TECH_NODE` 存字符串 `'28nm'` | `WHERE TECH_NODE=28` | `WHERE CAST(REPLACE(TECH_NODE,'nm','') AS INTEGER)=28` |
| **口径/时序**：`YLD_DAILY` 由夜间 job 生成 | 当日 08:00 前查昨日 | 避开空窗期，用 `date('now','-1 day')` 后的日期 |

> 这些规则**数据字典里没有**，只能靠领域知识文档显式沉淀。

---

### 2. OKF 理念

> **一个知识包 = 一个文件夹；一个知识点 = 一个 Markdown 文件
> （YAML frontmatter + 正文）；文件间用相对路径链接构成知识图谱。**

- frontmatter 用 `type` 枚举分类：`Table / Column / Metric / Spec`
- `related` 字段 + 正文相对路径链接 → 可被 `networkx` 构建成有向血缘图
- **隐性知识显式写进正文**，这正是普通数据字典做不到的

```
knowledge/
├── index.md                 # 全局导航入口
├── spec/                    # 规范：type枚举 / 命名 / 链接 / confidence 定义
│   ├── conventions.md
│   └── text2sql-rules.md    # SQL 生成规则（查表修正规则 + few-shot）
├── raw/dictionary/*.json   # L1：数据库自动抽取的数据字典（只读）
└── wiki/                    # L2：LLM（或 Mock）编译产物
    ├── tables/  ├── columns/  ├── metrics/  └── lineage/
```

#### 知识分层（L1 / L2）

| 层级 | 内容 | 生成方式 | 需要 AI？ |
|------|------|----------|-----------|
| **L1 raw** | 数据字典 JSON（表/字段/类型/主外键/行数） | 脚本自动抽取 | 否，纯机械 |
| **L2 wiki** | Markdown 知识（业务含义/隐性知识/SQL 注意） | **LLM 或 Mock** | 是（可离线演示） |

---

### 3. 核心设计：知识导航式 Text2SQL（vs 朴素 RAG）

对「SQL 正确性依赖某个字段的**精确值**」这类任务，向量分块检索并不可靠——
它可能把关键隐性知识切碎、漏掉。**FabWiki 采用「确定性读取」**：

```
用户问题
   │  ① 关键词定位（从知识索引挑出 2~5 张相关表）
   ▼
相关表知识点的【完整】Markdown（含隐性知识、SQL 注意事项）
   +   spec/text2sql-rules.md 规则（few-shot）
   │  ② 确定性读取全文，不做向量分块
   ▼
LLM 生成 SQL
   │  ③ 在 SQLite 上执行
   ▼
返回 DataFrame + SQL + 引用的知识文件列表
   │  ④ 失败 → 把报错回填给 LLM，重试一次
```

```python
def ask(self, question: str) -> Text2SQLResult:
    nodes = self.locate(question)                       # ① 定位相关表
    ctx = [f"===== {n.path} =====\n{self._table_full_text(n)}" for n in nodes]  # ② 全文
    ctx_text = "\n\n".join(ctx)
    if not config.LLM_AVAILABLE:
        sql, desc, _ = self._match_mock(question)       # Mock：内置示例→SQL
        return self._execute(question, sql, referenced, logs, mock=True)
    sql = self._llm_generate(question, ctx_text, referenced, logs)  # ③ 真实 LLM
    return self._execute(question, sql, referenced, logs, mock=False)
```

#### 血缘图谱：知识本身可被导航

`related` + 相对路径链接 → `networkx` 有向图 → `pyvis` 可视化：

```
WIP_LOT（在制批次） → WIP_LOT_HIST（过站历史） → YLD_DAILY（日良率汇总）
```

需要良率时沿下游找 `YLD_DAILY`，需要产品主档时沿上游找 `PRD_PRODUCT`。

---

### 4. 架构

```
┌─────────────── SQLite（模拟 Oracle 数仓）────────────────────────┐
│  WIP_LOT · WIP_LOT_HIST · PRD_PRODUCT · PRD_ROUTE                │
│  ENG_STEP · EQP_EQUIPMENT · QCS_DEFECT · YLD_DAILY             │
└───────────┬───────────────────────────────────────┬──────────────┘
            │ extractor（L1）                        │ raw 读取
            ▼                                        │
   raw/dictionary/*.json ──→ compiler（L2）──→  wiki/*.md
            （数据字典）        │  Mock/LLM        （隐性知识知识文件）
                               │                   │
                               └──► knowledge.py 索引（networkx 血缘图）
                                          │  确定性读取全文
                                          ▼
                                  text2sql.py（知识导航）
                                          │  生成 SQL + 执行
                                          ▼
                     Streamlit app：首页 / 知识浏览 / 血缘图谱 / Text2SQL
```

**核心闭环：**
1. **L1 抽取** — 从数仓自动抽取数据字典 → `raw/dictionary/`
2. **L2 编译** — LLM（或 Mock）把 raw「编译」为 wiki 知识文件，含隐性知识与
   Text2SQL 注意事项
3. **对话** — 知识浏览 / 血缘图谱 / 知识导航式 Text2SQL

---

### 5. 快速开始（3 条命令）

```bash
cd fabwiki
pip install -r requirements.txt
python scripts/init_db.py     # 建库 + 抽取 + 编译（Mock/LLM 自动，幂等，可重复执行）
streamlit run app.py          # 打开 http://localhost:8501（可用 --server.port 改端口）
```

> 也可在应用 **首页的「一键初始化」按钮** 完成同样的建库→抽取→编译。
> 想看血缘链路？在 **血缘图谱** 页选择 `WIP_LOT`，即可看到
> `WIP_LOT → WIP_LOT_HIST → YLD_DAILY`。

---

### 6. 运行模式：Mock / 真实 LLM

| 模式 | 触发条件 | 行为 |
|------|----------|------|
| **Mock（离线演示）** | 未配置 `LLM_API_KEY` | compiler 用内置高质量模板落盘；text2sql 用内置 5 个示例问题+SQL 映射 |
| **真实 LLM** | 配置 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | compiler 与 text2sql 走 OpenAI 兼容 API，Mock 内容被真实结果覆盖 |

```bash
cp .env.example .env
# 编辑 .env：填入 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL（DeepSeek 等任意兼容 API）
```

> **兼容**：若 `.env` 已有 `DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY`，无需额外配置，
> 项目自动兜底复用。**无 Key 时页面顶部会显示 `st.info` 提示处于 Mock 模式。**

---

### 7. 页面

| 页面 | 功能 |
|------|------|
| 🏠 **首页** | 项目介绍、OKF 理念、知识包统计（节点/边/confidence 分布）、一键初始化 |
| 📚 **知识浏览** | 按 type/tag/关键词过滤；渲染 frontmatter（表格）+ 正文（markdown）；关联知识点点击跳转 |
| 🕸️ **血缘图谱** | pyvis 全库知识链接图（节点按 type 着色）+ 单表 N 跳血缘子图 |
| 💬 **Text2SQL** | 知识导航对话；侧栏展示引用的知识文件；数据表格 / SQL（可复制）/ 执行日志三 Tab + 示例问题 |

---

### 8. 内置隐性知识（已写入 L2 文档）

- `LOT_STS`：`05`=Hold（待 MRB），**`99`=测试批次，任何统计必须排除**
- `DEFECT_CD` 前缀：`P*`=Particle、`S*`=Scratch、`M*`=Metal 残留；`DISPOSITION='SC'` 不计入产出
- `YLD_DAILY` 由夜间 job（`PKG_YLD_CALC`）生成，**当日 08:00 前昨日数据可能为空**
- `TECH_NODE` 存字符串 `'28nm'`，比较需 `CAST`
- `EQP STATUS_CD`：`M`=PM 保养中（算可用产能）

---

### 9. 实测演示

在 Text2SQL 页面问「**当前 Hold 中的批次数量？**」，知识导航后真实 LLM 生成的 SQL：

```sql
SELECT COUNT(*) AS HOLD_LOT_CNT
FROM WIP_LOT
WHERE LOT_STS = '05' AND LOT_STS <> '99';
```

模型不仅知道 `05=Hold`，还**自动排除了 `99` 测试批次**——这正是知识文件里
「隐性知识 + SQL 注意事项」被确定性读取后的效果。

---

### 10. 测试

```bash
python tests/test_smoke.py        # 或 pytest tests/test_smoke.py -v
```

覆盖全链路：建库 → 抽取 → Mock 编译 → 知识加载 → Mock text2sql，并断言
血缘链 `WIP_LOT→WIP_LOT_HIST→YLD_DAILY` 与 Hold 查询含 `'05'` 且排除 `'99'`。

---

### 11. 目录结构

```
fabwiki/
├── requirements.txt
├── .env.example
├── app.py                # Streamlit 入口（四页面）
├── config.py             # 路径 / LLM 配置 / Mock 开关
├── core/
│   ├── db.py             # SQLite 建库 + seed + 外键元数据
│   ├── extractor.py      # L1：抽取数据字典 → raw/ JSON
│   ├── compiler.py      # L2：Mock/LLM 编译知识 + lineage + index
│   ├── knowledge.py      # 知识包加载解析 + networkx 血缘图
│   ├── llm.py            # LLM 统一封装（超时/重试/降级 Mock）
│   └── text2sql.py       # 知识导航 Text2SQL
├── knowledge/            # OKF 知识包
├── scripts/init_db.py    # 一键建库 + seed（+ 抽取 + 编译）
└── tests/test_smoke.py   # 全链路冒烟测试
```

### 12. 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.10+ | 语言 |
| Streamlit | UI 四页面 |
| SQLite（模拟 Oracle） | 数仓，SQL 按标准写 |
| python-frontmatter | 解析 Markdown + YAML |
| networkx + pyvis | 血缘图谱构建与可视化 |
| openai SDK | OpenAI 兼容 API（base_url 可配置） |
| pandas / python-dotenv | 数据处理 / 配置加载 |

### 13. 进一步阅读

推荐先读：`knowledge/spec/conventions.md`（OKF 规范）与
`knowledge/spec/text2sql-rules.md`（SQL 生成规则 + few-shot）。
配套讲解与思路见项目 `blog/` 目录下的 CSDN 博客草稿。

---

<!-- tabs:end -->

<div id="english"></div>

---

# English

In a semiconductor **Fab**'s Oracle data warehouse, the MES / EAP / YMS schemas are
complex and full of **tacit knowledge** that lives only in domain experts' heads —
e.g. `LOT_STS='05'` means *Hold, pending MRB review*. Such knowledge is **not**
in the data dictionary, so Naive Text2SQL often produces wrong numbers.

**FabWiki** is an MVP built on **OKF (Open Knowledge Format)**: it "compiles"
*data dictionary + tacit knowledge + Text2SQL cautions* into a **navigable
knowledge graph**, and lets the LLM **deterministically read** the exact knowledge
it needs (instead of fuzzy vector chunk retrieval) before writing SQL.

It runs fully offline: **no API key required for a complete demo**.

- ✅ 8 Fab-style tables + 2 metrics, embedding 5 kinds of *tacit-knowledge traps*
- ✅ 4 Streamlit pages: Home / Browse / Lineage / Text2SQL
- ✅ Dual mode: **Mock** and **real LLM**, switch seamlessly
- ✅ Knowledge-Navigated Text2SQL: locate → deterministically read → generate → execute → retry-once

---

### 1. Why Naive Text2SQL Fails in a Fab

Writing SQL is easy; **making the model understand business semantics** is hard.
Typical *tacit-knowledge traps*:

| Trap | Wrong SQL | Right SQL |
|------|-----------|-----------|
| **Magic codes**: `LOT_STS`, `05`=Hold, **`99`=test lot** | `WHERE LOT_STS='05'` | `WHERE LOT_STS='05' AND LOT_STS<>'99'` |
| **Prefix codes**: `DEFECT_CD`, `P*`=Particle… | `WHERE DEFECT_CD='P12'` | `WHERE DEFECT_CD LIKE 'P%'` |
| **Field type**: `TECH_NODE` stores string `'28nm'` | `WHERE TECH_NODE=28` | `WHERE CAST(REPLACE(TECH_NODE,'nm','') AS INTEGER)=28` |
| **Timing / caliber**: `YLD_DAILY` from a nightly job | query yesterday before 08:00 | wait past the empty window; use `date('now','-1 day')` |

> None of these rules exist in the data dictionary — they must be explicitly
> captured in domain-knowledge documents.

---

### 2. The OKF Idea

> **A knowledge package = a folder; a knowledge point = a Markdown file
> (YAML frontmatter + body); files link to each other by relative paths to form
> a knowledge graph.**

- YAML `type` enum: `Table / Column / Metric / Spec`
- `related` field + relative links in body → build a directed graph with `networkx`
- **Tacit knowledge is written explicitly into the body** — something a plain
  data dictionary cannot do

```
knowledge/
├── index.md                 # Global navigation entry
├── spec/
│   ├── conventions.md       # conventions: type enum / naming / links / confidence
│   └── text2sql-rules.md    # SQL rules (lookup+few-shot)
├── raw/dictionary/*.json   # L1: auto-extracted data dictionary (read-only)
└── wiki/                    # L2: compiled by LLM (or Mock)
    ├── tables/  ├── columns/  ├── metrics/  └── lineage/
```

#### Knowledge layers (L1 / L2)

| Layer | Content | Producer | Needs AI? |
|-------|---------|----------|-----------|
| **L1 raw** | Data dictionary JSON (tables/columns/types/FK/row counts) | script | No, mechanical |
| **L2 wiki** | Markdown knowledge (meaning / tacit rules / SQL tips) | **LLM or Mock** | Yes (offline demo OK) |

---

### 3. Core Design: Knowledge-Navigated Text2SQL (vs naive RAG)

For tasks where **SQL correctness depends on the exact value of a field**,
vector chunk retrieval is unreliable — it may split or drop key tacit knowledge.
**FabWiki uses deterministic reading**:

```
User question
   │  ① keyword locate (pick 2~5 relevant tables from the index)
   ▼
The FULL Markdown of those knowledge points (tacit rules + SQL tips)
   +   spec/text2sql-rules.md (few-shot rules)
   │  ② deterministic read of the whole text, no vector chunking
   ▼
LLM generates SQL
   │  ③ execute against SQLite
   ▼
Return DataFrame + SQL + list of referenced knowledge files
   │  ④ on failure → feed the error back to the LLM, retry once
```

```python
def ask(self, question: str) -> Text2SQLResult:
    nodes = self.locate(question)                       # ① locate tables
    ctx = [f"===== {n.path} =====\n{self._table_full_text(n)}" for n in nodes]  # ② full text
    ctx_text = "\n\n".join(ctx)
    if not config.LLM_AVAILABLE:
        sql, desc, _ = self._match_mock(question)       # Mock: built-in Q→SQL
        return self._execute(question, sql, referenced, logs, mock=True)
    sql = self._llm_generate(question, ctx_text, referenced, logs)  # ③ real LLM
    return self._execute(question, sql, referenced, logs, mock=False)
```

#### Lineage graph: knowledge itself becomes navigable

`related` + relative-path links → `networkx` digraph → `pyvis` visualization:

```
WIP_LOT (work-in-progress lots) → WIP_LOT_HIST (step history) → YLD_DAILY (daily yield)
```

To get yield, walk downstream to `YLD_DAILY`; for product masters, walk upstream
to `PRD_PRODUCT`.

---

### 4. Architecture

```
┌─────────────── SQLite (simulating Oracle DW)──────────────────────────┐
│  WIP_LOT · WIP_LOT_HIST · PRD_PRODUCT · PRD_ROUTE                     │
│  ENG_STEP · EQP_EQUIPMENT · QCS_DEFECT · YLD_DAILY                    │
└───────────┬─────────────────────────────────────────┬─────────────────┘
            │ extractor (L1)                          │ raw read
            ▼                                          │
   raw/dictionary/*.json ──→ compiler (L2) ──→  wiki/*.md
            (dictionary)         │  Mock/LLM        (knowledge files)
                                 │                   │
                                 └──► knowledge.py index (networkx graph)
                                            │  deterministic read
                                            ▼
                                    text2sql.py (knowledge-navigated)
                                            │  generate SQL + execute
                                            ▼
                       Streamlit app: Home / Browse / Lineage / Text2SQL
```

**The core loop:**
1. **L1 extract** — auto-extract the data dictionary from the DW → `raw/dictionary/`
2. **L2 compile** — LLM (or Mock) "compiles" raw into wiki knowledge files
   (tacit rules + SQL tips)
3. **Chat** — browse / lineage graph / knowledge-navigated Text2SQL

---

### 5. Quick Start (3 commands)

```bash
cd fabwiki
pip install -r requirements.txt
python scripts/init_db.py     # build + extract + compile (Mock/LLM auto; idempotent)
streamlit run app.py          # open http://localhost:8501 (`--server.port` to change)
```

> You can also click the **"一键初始化 / Init" button** on the Home page.
> To see the lineage, open the **Lineage** page, select `WIP_LOT`, and follow
> `WIP_LOT → WIP_LOT_HIST → YLD_DAILY`.

---

### 6. Modes: Mock / Real LLM

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Mock (offline demo)** | no `LLM_API_KEY` | compiler writes built-in templates; text2sql uses 5 built-in Q→SQL examples |
| **Real LLM** | set `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | compiler & text2sql use an OpenAI-compatible API; Mock is overwritten by real output |

```bash
cp .env.example .env
# edit .env: fill LLM_API_KEY / LLM_BASE_URL / LLM_MODEL (DeepSeek or any compatible API)
```

> **Compatibility**: if your `.env` already has `DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY`,
> no extra config is needed — the project reuses them automatically.
> **Without a key**, the UI shows a `st.info` banner to indicate Mock mode.

---

### 7. Pages

| Page | Feature |
|------|---------|
| 🏠 **Home** | intro, OKF idea, knowledge stats (nodes/edges/confidence), one-click init |
| 📚 **Browse** | filter by type/tag/keyword; render frontmatter (table) + body (markdown); clickable links |
| 🕸️ **Lineage** | pyvis full knowledge graph (nodes colored by type) + per-table N-hop lineage |
| 💬 **Text2SQL** | knowledge-navigated chat; sidebar lists referenced files; table / SQL (copy) / log tabs + example questions |

---

### 8. Built-in Tacit Knowledge (written into L2 docs)

- `LOT_STS`: `05`=Hold (pending MRB), **`99`=test lot — must exclude in any stats**
- `DEFECT_CD` prefixes: `P*`=Particle, `S*`=Scratch, `M*`=Metal residue;
  `DISPOSITION='SC'` (Scrap) is **not** counted as output
- `YLD_DAILY` is generated by a nightly job (`PKG_YLD_CALC`); **before 08:00 the
  previous day's data may be empty**
- `TECH_NODE` stores a string like `'28nm'` — compare with `CAST`
- `EQP STATUS_CD`: `M`=Under PM (counts toward available capacity)

---

### 9. Live Demo

Ask *"How many lots are on Hold right now?"* in the Text2SQL page; the real LLM
(after knowledge navigation) produces:

```sql
SELECT COUNT(*) AS HOLD_LOT_CNT
FROM WIP_LOT
WHERE LOT_STS = '05' AND LOT_STS <> '99';
```

The model not only knows `05=Hold`, it **automatically excludes `99` test lots** —
exactly the effect of deterministically reading the *tacit-rules* section of the
knowledge file.

---

### 10. Tests

```bash
python tests/test_smoke.py        # or pytest tests/test_smoke.py -v
```

Covers the full pipeline: build → extract → Mock compile → knowledge load →
Mock text2sql, and asserts the lineage chain `WIP_LOT→WIP_LOT_HIST→YLD_DAILY`
and that the Hold query contains `'05'` while excluding `'99'`.

---

### 11. Directory Layout

```
fabwiki/
├── requirements.txt
├── .env.example
├── app.py                # Streamlit entry (4 pages)
├── config.py             # paths / LLM config / Mock switch
├── core/
│   ├── db.py             # SQLite build + seed + FK metadata
│   ├── extractor.py      # L1: extract dictionary → raw/ JSON
│   ├── compiler.py      # L2: Mock/LLM compile + lineage + index
│   ├── knowledge.py      # load/parse package + networkx lineage graph
│   ├── llm.py            # unified LLM wrapper (timeout/retry/Mock fallback)
│   └── text2sql.py       # knowledge-navigated Text2SQL
├── knowledge/            # OKF knowledge package
├── scripts/init_db.py    # one-key DB init + seed (+ extract + compile)
└── tests/test_smoke.py   # full-pipeline smoke test
```

### 12. Tech Stack

| Tech | Role |
|------|------|
| Python 3.10+ | language |
| Streamlit | UI (4 pages) |
| SQLite (simulates Oracle) | DW; standard SQL |
| python-frontmatter | parse Markdown + YAML |
| networkx + pyvis | lineage graph build & visualize |
| openai SDK | OpenAI-compatible API (configurable base_url) |
| pandas / python-dotenv | data / config |

### 13. Further Reading

Start with `knowledge/spec/conventions.md` (OKF conventions) and
`knowledge/spec/text2sql-rules.md` (SQL rules + few-shot).
The companion CSDN blog draft lives under the project's `blog/` directory.

---

## License

MIT — free to use, modify, and share. Pull requests welcome.

## 致谢 / Acknowledgments

Built on OKF (Open Knowledge Format) ideas and the Streamlit / pyvis / networkx
ecosystems.
# 🏭 Fab Ontology Text2SQL（半导体晶圆厂 MVP）

一个基于 **Palantir Ontology 三层架构思想** 的 FAB Text2SQL 最小可运行项目。
摒弃「自然语言直接翻译 SQL」的脆弱模式，改为 **语义层做概念映射、动力层做模板化查
询、动态层做数据执行** 的三段式架构，让 LLM 只负责意图识别与参数提取，**绝不自由
编写 JOIN / WHERE**。

## 一、架构总览（Palantir Ontology 映射）

```
用户自然语言 "帮我查一下 3号机 上周的良率趋势"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ ① 语义层 Semantic Layer （ontology_dict.json + Schema 解析器） │
│    业务黑话 → 字段：3号机→EQP-003；良率→YIELD_RATE；         │
│    上周→最近7天；膜厚异常→FILM_THICKNESS∉[4500,5000]        │
│    ✂ Schema 解析器：只把命中的片段注入给 LLM，省 Token       │
├─────────────────────────────────────────────────────────────┤
│ ② 动力层 Kinetic Layer （FabQueryAgent）                      │
│    LLM 输出结构化 JSON 计划（object/metric/trend/设备/时间）   │
│    离线时回退本地规则引擎                                    │
├─────────────────────────────────────────────────────────────┤
│ ③ 动力层模板库 （sql_templates/*.sql）                        │
│    12 个预定义查询模板，参数白名单校验 + 参数化绑定（防注入）   │
├─────────────────────────────────────────────────────────────┤
│ ④ 动态层 Dynamic Layer （mock_db.py → data/fab.db）           │
│    4 张核心表：EQUIPMENT / LOT_INFO /                        │
│               WAFER_METROLOGY / PROCESS_LOG                 │
└─────────────────────────────────────────────────────────────┘
```

| 层 | 文件 | 职责 |
|---|---|---|
| 语义层 | `ontology_dict.json`、`ontology.py::OntologyDictionary` | 业务概念 ↔ 字段映射、Schema 解析器（按问题过滤注入片段） |
| 动力层 | `ontology.py::FabQueryAgent`、`sql_templates/*.sql` | 意图提取（LLM/规则）→ 模板选择 → 参数化 SQL |
| 动态层 | `mock_db.py` | SQLite 建表 + Mock 数据（相对「今天」生成，随时可查「上周」） |
| 展示壳 | `app.py` | Streamlit 聊天界面 + 「思考链 Trace」面板 |

## 二、目录结构

```
fab_ontology_text2sql/
├── app.py                    # Streamlit 主程序（UI + Trace 面板）
├── ontology.py               # 语义层（OntologyDictionary）+ 动力层（FabQueryAgent）
├── mock_db.py                # 动态层：SQLite 建表 + Mock 数据生成
├── ontology_dict.json        # 语义层：晶圆厂本体字典（业务黑话 ↔ 字段）
├── sql_templates/            # 动力层：预定义查询模板库
│   ├── get_yield_trend.sql            良率趋势（按日）
│   ├── get_equipment_yield.sql        平均良率 / 按设备排名
│   ├── get_film_stats.sql             膜厚统计
│   ├── get_film_thickness_trend.sql   膜厚趋势
│   ├── get_film_abnormal.sql          膜厚异常晶圆清单
│   ├── get_defect_stats.sql           缺陷统计
│   ├── get_defect_high.sql            缺陷偏高晶圆清单
│   ├── get_lot_status.sql             批次详情
│   ├── get_lot_list.sql               批次列表
│   ├── get_process_log_by_lot.sql     批次工艺日志
│   ├── get_process_log_by_equipment.sql 设备工艺日志
│   └── get_equipment_status.sql       设备状态
├── requirements.txt          # 依赖
├── .env                      # DeepSeek / DashScope API 配置（已存在）
└── data/fab.db               # 运行时自动生成的 SQLite 数据库
```

## 三、快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动（.env 中配置 DeepSeek API；未配置也会自动回退离线规则引擎）
streamlit run app.py
```

> 侧边栏可实时开关 LLM、改模型/Base URL/API Key（OpenAI SDK 兼容格式，
> 可换成任意本地 vLLM / Ollama / 云端服务）。

## 四、示例问题

| 自然语言 | 语义层命中 | 动力层模板 |
|---|---|---|
| 帮我查一下 3号机 上周的良率趋势 | 别名 3号机、指标 良率、时间 上周 | get_yield_trend.sql |
| 膜厚异常的晶圆有哪些？ | 指标 膜厚、条件 膜厚异常 | get_film_abnormal.sql |
| 各设备的平均良率排名 | 指标 良率 | get_equipment_yield.sql |
| LOT-2026-001 的工艺日志 | 对象 工艺、批次号 | get_process_log_by_lot.sql |
| 缺陷偏高的晶圆有哪些 | 指标 缺陷、条件 缺陷偏高 | get_defect_high.sql |
| 当前所有设备的状态 | 对象 设备 | get_equipment_status.sql |

## 五、设计要点

1. **LLM 不写 SQL**：LLM 只输出结构化 JSON（object/metric/trend/equipment/…），
   任何非法值都会被 `_validate_plan` 白名单过滤置空。
2. **SQL 全部预定义**：12 个 `sql_templates/*.sql`，Agent 按计划选择模板并填充
   `?` 占位参数；可选设备过滤用 `EQP_ID = COALESCE(?, EQP_ID)` 实现，绝无字符串拼接。
3. **省 Token**：Schema 解析器只把与问题相关的本体片段注入给 LLM（对话里可查看
   「注入 N 条 / 共 M 条」）。
4. **离线可用**：未配置 API Key 或调用失败时自动回退本地规则引擎。
5. **Mock 数据贴近业务**：约 4% 晶圆膜厚异常、少量缺陷偏高、良率与缺陷负相关。

## 六、扩展方向

- 增加权限层（按用户/部门过滤客户、产品字段）
- 把规则引擎替换为 Few-shot Prompt 或微调的小模型
- 结果缓存 + 术语表（Glossary）支持别名扩充
- 接入真实 MES/APC 数据源替换 mock_db
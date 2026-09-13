"""L2 编译器：将 L1 raw 数据字典"编译"为 wiki 知识 Markdown。

输入一张表（或指标）的 raw JSON → 构造 prompt 调 LLM（也可用 Mock 模板）
→ 生成符合 OKF 规范的 .md；同时生成 lineage 文件并刷新 index.md。

Mock 模式（一等公民）：内置高质量模板，保证离线可完整演示。
Mock 内容即是"LLM 应该生成的样子"，已写足全部隐性知识。
"""
from __future__ import annotations

from pathlib import Path

import config
from core import db, extractor
from core.llm import chat_complete

# 各 table 的隐性知识说明（与 db._SCHEMA 注释一并对齐，作为 prompt 上下文/模板依据）
_TABLE_HINTS: dict[str, str] = {
    "WIP_LOT": ("LOT_STS 隐性编码：01=Released，03=Running，05=Hold(待MRB评审)，"
                "07=Terminated，99=测试批次——统计查询必须排除 99。"),
    "WIP_LOT_HIST": "QTY_OUT=过站产出，DEFECT_CNT=本步缺陷数；按 LOT_ID 关联 WIP_LOT。",
    "PRD_PRODUCT": "TECH_NODE 为字符串如'28nm'，数值比较需 CAST。",
    "PRD_ROUTE": "STEP_SEQ 为工序顺序；STEP_ID 关联 ENG_STEP。",
    "ENG_STEP": "STEP_GRP 枚举 PHOTO/ETCH/CVD/CMP/IMP/METAL；CRITICAL_FLAG='Y' 为关键工序。",
    "EQP_EQUIPMENT": "STATUS_CD 隐性编码：R=Run,I=Idle,D=Down,M=PM保养中(算可用产能)。",
    "QCS_DEFECT": ("DEFECT_CD 前缀规则：P*=Particle,S*=Scratch,M*=Metal残留；"
                   "DISPOSITION='SC'(Scrap)的晶圆不计入产出。"),
    "YLD_DAILY": "由夜间 job(存储过程 PKG_YLD_CALC)生成，当日08:00前查询昨日数据可能为空。",
}


# --------------------------------------------------------------------------
# Mock 模板：8 张表 + 2 个指标，均为高质量 markdown（离线演示基线）
# --------------------------------------------------------------------------
def _table_md(table: str, row_count: int) -> str:
    """返回某张表的 Mock 模板 markdown。"""
    # 各表正文；未单独定制时给通用骨架
    bodies = {
        "WIP_LOT": """## 业务含义

在制品（WIP）批次主档，记录晶圆厂当前在制的每一批次。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| LOT_ID | TEXT | 批次号（PK） | |
| PRODUCT_ID | TEXT | 产品号，关联 PRD_PRODUCT | |
| STAGE_CD | TEXT | 当前工序 | |
| LOT_STS | TEXT | 批次状态 | **05=Hold(待MRB评审)；99=测试批次，统计必须排除** |
| QTY_IN | INTEGER | 投入晶圆数 | |
| WAFER_CNT | INTEGER | 批次晶圆数 | |
| CREATE_DT | TEXT | 建批时间 | |
| LAST_MOD_DT | TEXT | 最后修改时间 | |

### LOT_STS 编码对照（隐性知识）

| 编码 | 含义 | 说明 |
|------|------|------|
| 01 | Released | 已释放 |
| 03 | Running | 生产中 |
| 05 | Hold | 待 MRB 评审 |
| 07 | Terminated | 终止 |
| **99** | 测试批次 | **任何统计查询必须排除 `LOT_STS='99'`** |

## 血缘

- 下游：批次过站历史 [WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md)、
  缺陷 [QCS_DEFECT](../wiki/tables/QCS_DEFECT.md)
- 上游：产品主档 [PRD_PRODUCT](../wiki/tables/PRD_PRODUCT.md)

## Text2SQL 注意事项

- 统计在制品数量/良率时必须排除测试批次：`WHERE LOT_STS <> '99'`。
- 查 Hold 批次用 `LOT_STS='05'`，同时仍要排除 `99`。

## 来源

L1 数据字典 `raw/dictionary/WIP_LOT.json`（Mock seed 基线）。
""",
        "WIP_LOT_HIST": """## 业务含义

批次过站历史：批次在每一道工序制造时的记录（何时、在哪台设备、产出多少、本步缺陷数）。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| HIST_ID | INTEGER | 历史流水号（PK） | |
| LOT_ID | TEXT | 批次号，FK→WIP_LOT | |
| STEP_ID | TEXT | 工序，FK→ENG_STEP | |
| EQP_ID | TEXT | 设备，FK→EQP_EQUIPMENT | |
| TRACK_OUT_DT | TEXT | 过站（Track Out）时间 | |
| QTY_OUT | INTEGER | 本步产出晶圆数 | |
| DEFECT_CNT | INTEGER | 本步缺陷数 | 异常高需排查 |

## 血缘

- 上游：批次 [WIP_LOT](../wiki/tables/WIP_LOT.md)、工序 [ENG_STEP](../wiki/tables/ENG_STEP.md)、设备 [EQP_EQUIPMENT](../wiki/tables/EQP_EQUIPMENT.md)
- 下游：日良率汇总 [YLD_DAILY](../wiki/tables/YLD_DAILY.md)（由加工数据汇聚而来）

## Text2SQL 注意事项

- 统计设备产出/缺陷按下游聚合 `EQP_ID`、`STEP_ID` 时用 `SUM(QTY_OUT)`。
- 时段过滤用 `TRACK_OUT_DT`。

## 来源

L1 数据字典 `raw/dictionary/WIP_LOT_HIST.json`（Mock seed 基线）。
""",
        "PRD_PRODUCT": """## 业务含义

产品主档，定义晶圆厂可生产的产品及其工艺特征。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| PRODUCT_ID | TEXT | 产品号（PK） | |
| PRODUCT_NM | TEXT | 产品名称 | |
| TECH_NODE | TEXT | 技术节点，存字符串如 '28nm' | **数值比较需 CAST** |
| DIE_SIZE | REAL | 管芯尺寸 | |
| LAYER_CNT | INTEGER | 光刻层数 | |

## 血缘

- 上游：被 [WIP_LOT](../wiki/tables/WIP_LOT.md)、[WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md)、[YLD_DAILY](../wiki/tables/YLD_DAILY.md) 引用。

## Text2SQL 注意事项

- `TECH_NODE` 是字符串 '28nm'，按数字比较要用
  `CAST(REPLACE(TECH_NODE,'nm','') AS INTEGER) = 28`。

## 来源

L1 数据字典 `raw/dictionary/PRD_PRODUCT.json`（Mock seed 基线）。
""",
        "PRD_ROUTE": """## 业务含义

产品工艺路线：某产品从投片到完工必须经过的工序顺序。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| ROUTE_ID | INTEGER | 路线流水（PK） | |
| PRODUCT_ID | TEXT | 产品，FK→PRD_PRODUCT | |
| STEP_SEQ | INTEGER | 工序顺序号 | 越小编号越靠前 |
| STEP_ID | TEXT | 工序，FK→ENG_STEP | |

## 血缘

- 上游：产品 [PRD_PRODUCT](../wiki/tables/PRD_PRODUCT.md)、工序 [ENG_STEP](../wiki/tables/ENG_STEP.md)。

## Text2SQL 注意事项

- 需要"产品工艺顺序"时按 `STEP_SEQ` 排序；不要按加工表臆测工序顺序。

## 来源

L1 数据字典 `raw/dictionary/PRD_ROUTE.json`（Mock seed 基线）。
""",
        "ENG_STEP": """## 业务含义

工序（Step）主档，定义制造的每一道工序及其归属工艺组。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| STEP_ID | TEXT | 工序号（PK） | |
| STEP_NM | TEXT | 工序名 | |
| STEP_GRP | TEXT | 工艺组 | 枚举：PHOTO/ETCH/CVD/CMP/IMP/METAL |
| CRITICAL_FLAG | TEXT | 关键工序标识 | 'Y'=关键工序 |

## 血缘

- 上游：被 [WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md)、[QCS_DEFECT](../wiki/tables/QCS_DEFECT.md)、[PRD_ROUTE](../wiki/tables/PRD_ROUTE.md) 引用。

## Text2SQL 注意事项

- 按工艺组统计（如 PHOTO 缺陷）要用 `ENG_STEP.STEP_GRP=...` 关联，而不是光看 STEP_ID。

## 来源

L1 数据字典 `raw/dictionary/ENG_STEP.json`（Mock seed 基线）。
""",
        "EQP_EQUIPMENT": """## 业务含义

设备主档，定义晶圆厂所有生产设备的类型与当前状态。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| EQP_ID | TEXT | 设备号（PK） | |
| EQP_NM | TEXT | 设备名 | |
| EQP_TYPE | TEXT | 设备类型 | 如 LITHO / ETCH |
| TOOL_GRP | TEXT | 工具组 | 对应工艺组 |
| STATUS_CD | TEXT | 状态编码 | **M=PM保养中(算可用产能)** |

### STATUS_CD 编码对照（隐性知识）

| 编码 | 含义 | 备注 |
|------|------|------|
| R | Run | 运行中 |
| I | Idle | 空闲 |
| D | Down | 故障停机 |
| **M** | PM 保养中 | **统计可用产能时计入** |

## 血缘

- 上游：被 [WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md) 引用。

## Text2SQL 注意事项

- 算"可用产能/可用设备数"时用 `STATUS_CD IN ('R','I','M')`，其中 M 也算。

## 来源

L1 数据字典 `raw/dictionary/EQP_EQUIPMENT.json`（Mock seed 基线）。
""",
        "QCS_DEFECT": """## 业务含义

缺陷记录（QCS 检查系统），记录批次在某工序检查出的缺陷及处置结论。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| DEFECT_ID | INTEGER | 缺陷流水（PK） | |
| LOT_ID | TEXT | 批次，FK→WIP_LOT | |
| STEP_ID | TEXT | 工序，FK→ENG_STEP | |
| DEFECT_CD | TEXT | 缺陷编码 | **前缀规则：P*=Particle 等** |
| DEFECT_CNT | INTEGER | 缺陷数量 | |
| INSPECT_DT | TEXT | 检查日期 | |
| DISPOSITION | TEXT | 处置结论 | **SC(Scrap)不计入产出** |

### DEFECT_CD 前缀规则（隐性知识）

| 前缀 | 含义 |
|------|------|
| P* | Particle（颗粒） |
| S* | Scratch（划伤） |
| M* | Metal 残留（金属残留） |

## 血缘

- 上游：批次 [WIP_LOT](../wiki/tables/WIP_LOT.md)、工序 [ENG_STEP](../wiki/tables/ENG_STEP.md)。

## Text2SQL 注意事项

- 按缺陷类别统计用 `DEFECT_CD LIKE 'P%'` 等前缀匹配。
- 计算产出/良率时排除 `DISPOSITION='SC'` 的晶圆。

## 来源

L1 数据字典 `raw/dictionary/QCS_DEFECT.json`（Mock seed 基线）。
""",
        "YLD_DAILY": """## 业务含义

日良率汇总，由夜间 job（存储过程 **PKG_YLD_CALC**）每日生成，按产品×工艺组汇总。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| STAT_DT | TEXT | 统计日期（PK 之一） | **夜间生成，当日 08:00 前昨日数据可能为空** |
| PRODUCT_ID | TEXT | 产品，FK→PRD_PRODUCT | |
| STEP_GRP | TEXT | 工艺组 | 与 ENG_STEP.STEP_GRP 对齐 |
| INPUT_WAFER | INTEGER | 投入晶圆 | |
| OUTPUT_WAFER | INTEGER | 产出晶圆 | 已排除 SC |
| YLD_RATE | REAL | 良率 = OUTPUT/INPUT | 直接用即可 |

## 血缘

- 上游：由批次过站数据汇聚而来 [WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md)，
  关联产品 [PRD_PRODUCT](../wiki/tables/PRD_PRODUCT.md)。

## Text2SQL 注意事项

- 查询"昨日/今日"良率时注意：数据由夜间 job 生成，**当日 08:00 前查询昨日数据可能为空**。
- 计算良率直接用 `YLD_RATE`，不要再用 OUTPUT/INPUT 重算（口径已定）。

## 来源

L1 数据字典 `raw/dictionary/YLD_DAILY.json`（Mock seed 基线）。
""",
    }
    body = bodies.get(table, _generic_table_body(table))
    return _table_frontmatter(table, row_count) + body


def _generic_table_body(table: str) -> str:
    return f"""## 业务含义

{table} 的通用知识占位（Mock 模板未定制）。

## 关键字段

见来源 raw JSON。

## 血缘

见 lineage 文件。

## Text2SQL 注意事项

无。

## 来源

L1 数据字典 `raw/dictionary/{table}.json`。
"""


_DATE = "2026-09-13"
_TAG_BY_GRP = {"WIP_LOT": "[wip, 在制品, fab]", "WIP_LOT_HIST": "[wip, 过站, fab]",
               "PRD_PRODUCT": "[产品, 主档]", "PRD_ROUTE": "[产品, 工艺路线]",
               "ENG_STEP": "[工程, 工序]", "EQP_EQUIPMENT": "[设备, 主档]",
               "QCS_DEFECT": "[质量, 缺陷]", "YLD_DAILY": "[良率, 日汇总]"}
_RELATED_BY_TABLE = {
    "WIP_LOT": ["wiki/tables/WIP_LOT_HIST.md", "wiki/tables/QCS_DEFECT.md", "wiki/tables/PRD_PRODUCT.md",
                "wiki/columns/WIP_LOT.LOT_STS.md"],
    "WIP_LOT_HIST": ["wiki/tables/WIP_LOT.md", "wiki/tables/ENG_STEP.md", "wiki/tables/EQP_EQUIPMENT.md", "wiki/tables/YLD_DAILY.md",
                     "wiki/columns/WIP_LOT_HIST.QTY_OUT.md", "wiki/columns/WIP_LOT_HIST.DEFECT_CNT.md"],
    "PRD_PRODUCT": ["wiki/tables/WIP_LOT.md", "wiki/tables/YLD_DAILY.md", "spec/text2sql-rules.md",
                    "wiki/columns/PRD_PRODUCT.TECH_NODE.md"],
    "PRD_ROUTE": ["wiki/tables/PRD_PRODUCT.md", "wiki/tables/ENG_STEP.md"],
    "ENG_STEP": ["wiki/tables/WIP_LOT_HIST.md", "wiki/tables/QCS_DEFECT.md", "wiki/tables/PRD_ROUTE.md"],
    "EQP_EQUIPMENT": ["wiki/tables/WIP_LOT_HIST.md",
                      "wiki/columns/EQP_EQUIPMENT.STATUS_CD.md"],
    "QCS_DEFECT": ["wiki/tables/WIP_LOT.md", "wiki/tables/ENG_STEP.md", "wiki/metrics/yield-rate.md",
                   "wiki/columns/QCS_DEFECT.DEFECT_CD.md", "wiki/columns/QCS_DEFECT.DISPOSITION.md"],
    "YLD_DAILY": ["wiki/tables/WIP_LOT_HIST.md", "wiki/tables/PRD_PRODUCT.md", "wiki/metrics/yield-rate.md",
                  "wiki/columns/YLD_DAILY.STAT_DT.md", "wiki/columns/YLD_DAILY.YLD_RATE.md"],
}

# 含有隐性知识的字段（需要生成 Column 级知识文件）
# key: "TABLE.COLUMN", value: 隐性知识要点
_COLUMN_WITH_TACIT = {
    "WIP_LOT.LOT_STS": "批次状态编码，含魔法数字陷阱（05=Hold, 99=测试批次必须排除）",
    "PRD_PRODUCT.TECH_NODE": "技术节点存字符串如'28nm'，数值比较需 CAST",
    "EQP_EQUIPMENT.STATUS_CD": "设备状态编码，M=PM保养中（算可用产能）",
    "QCS_DEFECT.DEFECT_CD": "缺陷编码前缀规则（P*=Particle, S*=Scratch, M*=Metal残留）",
    "QCS_DEFECT.DISPOSITION": "处置结论，SC=Scrap不计入产出",
    "YLD_DAILY.STAT_DT": "统计日期，夜间job生成，当日08:00前昨日数据可能为空",
    "YLD_DAILY.YLD_RATE": "良率字段，已由PKG_YLD_CALC计算好，直接使用即可",
    "WIP_LOT_HIST.QTY_OUT": "本步产出晶圆数，统计产出时用SUM",
    "WIP_LOT_HIST.DEFECT_CNT": "本步缺陷数，异常高需排查",
}


def _table_frontmatter(table: str, row_count: int) -> str:
    tags = _TAG_BY_GRP.get(table, "[fab]")
    related = _RELATED_BY_TABLE.get(table, [])
    related_yaml = "\n".join(f"  - {r}" for r in related)
    return f"""---
title: "{table} 表知识"
type: Table
resource: {table}
tags: {tags}
confidence: seed
related:
{related_yaml}
updated: {_DATE}
---

# {table} 表

> L2 编译产物（Mock seed 基线）· 当前约 {row_count} 行

"""


def _metric_md(metric: dict) -> str:
    """指标 Mock 模板。metric = {resource, title, tags, related, body}"""
    related_yaml = "\n".join(f"  - {r}" for r in metric["related"])
    return f"""---
title: "{metric['title']}"
type: Metric
resource: {metric['resource']}
tags: {metric['tags']}
confidence: seed
related:
{related_yaml}
updated: {_DATE}
---

# {metric['title']}

> L2 编译产物（指标口径）· Mock seed 基线
{metric['body']}
"""


METRICS = [
    {
        "resource": "wafer-yield-rate",
        "title": "晶圆良率",
        "tags": "[良率, KPI]",
        "related": ["wiki/tables/YLD_DAILY.md", "wiki/tables/QCS_DEFECT.md",
                    "wiki/tables/PRD_PRODUCT.md"],
        "body": """## 业务含义

产品在某工艺组（或全厂）的晶圆良率，衡量产出质量的核心 KPI。

## 计算口径

```
良率 = OUTPUT_WAFER / INPUT_WAFER
```
直接取 [YLD_DAILY](../wiki/tables/YLD_DAILY.md) 的 `YLD_RATE` 字段即可，已被 _PKG_YLD_CALC_ 汇总好。

## 隐性知识 / 陷阱

- **排除测试批次**：任何良率统计必须排除 `WIP_LOT.LOT_STS='99'`。
- **排除 Scrap**：产出侧已排除 `QCS_DEFECT.DISPOSITION='SC'` 的晶圆。
- **TECH_NODE 需 CAST**：按技术节点维度对比时用
  `CAST(REPLACE(TECH_NODE,'nm','') AS INTEGER)`。
- **夜间 job 空窗**：`YLD_DAILY` 为夜间生成，当日 08:00 前查昨日可能为空。

## 血缘

- 依赖 [YLD_DAILY](../wiki/tables/YLD_DAILY.md)；口径涉及 [QCS_DEFECT](../wiki/tables/QCS_DEFECT.md)。

## Text2SQL 注意事项

- 趋势查询：`SELECT stat_dt, product_id, AVG(yld_rate) FROM YLD_DAILY ... GROUP BY ...`。
- 较小样本用 `AVG(YLD_RATE)` 而非对行数取平均。
""",
    },
    {
        "resource": "hold-lot-count",
        "title": "Hold 批次数量",
        "tags": "[在制品, KPI, MRB]",
        "related": ["wiki/tables/WIP_LOT.md"],
        "body": """## 业务含义

当前处于 Hold（待 MRB 评审）状态的批次数量，反映在制品风险水位。

## 计算口径

```sql
SELECT COUNT(*) FROM WIP_LOT
WHERE LOT_STS = '05'
  AND LOT_STS <> '99';
```

## 隐性知识 / 陷阱

- **LOT_STS='05' = Hold**，待 MRB 评审。
- **必须排除 '99' 测试批次**，否则把测试数据算进风险批次。
- 如需按产品/工序细分，GROUP BY PRODUCT_ID / STAGE_CD。

## 血缘

- 依赖 [WIP_LOT](../wiki/tables/WIP_LOT.md)。

## Text2SQL 注意事项

- 一定带 `LOT_STS <> '99'` 过滤（规则见 [text2sql-rules](../spec/text2sql-rules.md)）。
""",
    },
]


# --------------------------------------------------------------------------
# LLM 真实编译
# --------------------------------------------------------------------------
_COLUMN_MOCK_BODIES = {
    "WIP_LOT.LOT_STS": """## 业务含义

批次状态编码，标识晶圆批次当前所处的生命周期阶段。

## 编码对照（隐性知识）

| 编码 | 含义 | 说明 |
|------|------|------|
| 01 | Released | 已释放，等待投片 |
| 03 | Running | 生产中，正在某工序加工 |
| 05 | Hold | 待 MRB 评审，暂停生产 |
| 07 | Terminated | 已终止，不再继续生产 |
| **99** | 测试批次 | **任何统计查询必须排除 `LOT_STS='99'`** |

## Text2SQL 注意事项

- 统计在制品数量、良率、Hold 批次等，**必须**加上 `WHERE LOT_STS <> '99'` 排除测试批次。
- 查 Hold 批次用 `LOT_STS = '05'`，同时仍要排除 `99`。
- 不要只按字面意思查 `LOT_STS = 'Hold'`，存储值是编码数字。

## 血缘

- 所属表：[WIP_LOT](../tables/WIP_LOT.md)
- 相关指标：[Hold 批次数量](../../metrics/hold-lot-count.md)
""",
    "PRD_PRODUCT.TECH_NODE": """## 业务含义

产品的技术节点（工艺代），如 28nm、22nm 等，代表芯片制造的工艺水平。

## 存储格式（隐性知识）

- 字段类型为 TEXT，存储格式如 `'28nm'`、`'22nm'`、`'65nm'`。
- **不能直接按数字比较**，如 `WHERE TECH_NODE = 28` 会报错或查不到。

## Text2SQL 注意事项

- 按数值比较时用 `CAST(REPLACE(TECH_NODE, 'nm', '') AS INTEGER) = 28`。
- 按字符串精确匹配：`WHERE TECH_NODE = '28nm'`。
- 按工艺代范围：`CAST(REPLACE(TECH_NODE, 'nm', '') AS INTEGER) <= 28`。

## 血缘

- 所属表：[PRD_PRODUCT](../tables/PRD_PRODUCT.md)
""",
    "EQP_EQUIPMENT.STATUS_CD": """## 业务含义

设备当前状态编码，反映设备的可用情况。

## 编码对照（隐性知识）

| 编码 | 含义 | 是否计入可用产能 |
|------|------|-----------------|
| R | Run（运行中） | ✅ 是 |
| I | Idle（空闲） | ✅ 是 |
| D | Down（故障停机） | ❌ 否 |
| **M** | PM 保养中 | **✅ 是**（保养是计划性的，不算故障停机） |

## Text2SQL 注意事项

- 统计可用设备数：`WHERE STATUS_CD IN ('R', 'I', 'M')`。
- 注意 **M（PM 保养中）也要算可用产能**，不要只查 R 和 I。
- 统计故障设备：`WHERE STATUS_CD = 'D'`。

## 血缘

- 所属表：[EQP_EQUIPMENT](../tables/EQP_EQUIPMENT.md)
""",
    "QCS_DEFECT.DEFECT_CD": """## 业务含义

缺陷编码，标识缺陷的类型。编码有前缀约定，同一前缀代表同一大类缺陷。

## 前缀规则（隐性知识）

| 前缀 | 含义 | 示例 |
|------|------|------|
| P | Particle（颗粒污染） | P01, P12, P20 |
| S | Scratch（划伤） | S03, S15 |
| M | Metal 残留（金属残留） | M02, M11 |

## Text2SQL 注意事项

- 按缺陷大类统计用前缀匹配：`WHERE DEFECT_CD LIKE 'P%'`（颗粒缺陷）。
- **不要**用精确全码匹配来统计大类，如 `WHERE DEFECT_CD = 'P12'` 只能查到一种具体缺陷。
- 具体缺陷编号随工艺迭代可能增加，按前缀统计更稳健。

## 血缘

- 所属表：[QCS_DEFECT](../tables/QCS_DEFECT.md)
- 相关指标：[晶圆良率](../../metrics/wafer-yield-rate.md)
""",
    "QCS_DEFECT.DISPOSITION": """## 业务含义

缺陷处置结论，表示发现缺陷后晶圆的最终处理方式。

## 编码对照（隐性知识）

| 编码 | 含义 | 是否计入产出 |
|------|------|-------------|
| OK | 正常通过 | ✅ 是 |
| RS | Rework（返工） | ✅ 是（返工后重新入线） |
| **SC** | Scrap（报废） | **❌ 否**（报废晶圆不计入产出） |

## Text2SQL 注意事项

- 计算产出/良率时排除报废：`WHERE DISPOSITION <> 'SC'`。
- `YLD_DAILY` 表的 `OUTPUT_WAFER` 已经排除了 SC，直接用即可。
- 统计报废率：`SUM(CASE WHEN DISPOSITION='SC' THEN DEFECT_CNT ELSE 0 END) / SUM(DEFECT_CNT)`。

## 血缘

- 所属表：[QCS_DEFECT](../tables/QCS_DEFECT.md)
- 相关指标：[晶圆良率](../../metrics/wafer-yield-rate.md)
""",
    "YLD_DAILY.STAT_DT": """## 业务含义

良率统计日期，作为 YLD_DAILY 表的联合主键之一。

## 生成机制（隐性知识）

- `YLD_DAILY` 由夜间 job `PKG_YLD_CALC` 生成，统计前一天的良率数据。
- **当日 08:00 之前查询昨日数据可能为空**，因为 job 还没跑完。

## Text2SQL 注意事项

- 查询"昨日良率"时，为避开空窗期，建议查 `date('now', '-2 day')` 之前的数据。
- 或用 `STAT_DT >= date('now', '-3 day') AND STAT_DT < date('now', '-1 day')` 取最近完整的两天。
- 当日数据（`STAT_DT = date('now')`）肯定为空，不要查。

## 血缘

- 所属表：[YLD_DAILY](../tables/YLD_DAILY.md)
- 相关指标：[晶圆良率](../../metrics/wafer-yield-rate.md)
""",
    "YLD_DAILY.YLD_RATE": """## 业务含义

当日良率，即产出晶圆数 / 投入晶圆数。

## 口径说明（隐性知识）

- 由夜间 job `PKG_YLD_CALC` 预先计算好，直接使用即可。
- 已排除 `DISPOSITION='SC'`（报废）的晶圆。
- 已排除 `LOT_STS='99'`（测试批次）。

## Text2SQL 注意事项

- 直接用 `YLD_RATE` 字段，**不要**自己用 `OUTPUT_WAFER / INPUT_WAFER` 重算（口径已定）。
- 多日平均用 `AVG(YLD_RATE)`，而不是 `SUM(OUTPUT_WAFER) / SUM(INPUT_WAFER)`（除非明确要加权）。
- 取值范围 0~1，显示时可乘 100 转百分比。

## 血缘

- 所属表：[YLD_DAILY](../tables/YLD_DAILY.md)
- 相关指标：[晶圆良率](../../metrics/wafer-yield-rate.md)
""",
    "WIP_LOT_HIST.QTY_OUT": """## 业务含义

本步（某批次在某工序）产出的晶圆数量。

## 口径说明

- 为过站（Track Out）时的实际产出数。
- 可能小于投入数（因为有报废、缺陷等）。

## Text2SQL 注意事项

- 统计某设备/工序的总产出用 `SUM(QTY_OUT)`。
- 按时间段过滤用 `TRACK_OUT_DT`。
- 按设备统计用 `GROUP BY EQP_ID`。

## 血缘

- 所属表：[WIP_LOT_HIST](../tables/WIP_LOT_HIST.md)
""",
    "WIP_LOT_HIST.DEFECT_CNT": """## 业务含义

本步（某批次在某工序）检测出的缺陷总数。

## 口径说明

- 为本步的缺陷计数，不是累计缺陷数。
- 缺陷数量异常高时需排查工艺或设备问题。

## Text2SQL 注意事项

- 统计某工序总缺陷用 `SUM(DEFECT_CNT)`。
- 缺陷 Top N 查询：按 `STEP_ID` 或 `DEFECT_CD` 聚合后排序。
- 结合 `QCS_DEFECT` 表可查更详细的缺陷分类。

## 血缘

- 所属表：[WIP_LOT_HIST](../tables/WIP_LOT_HIST.md)
""",
}


def _column_frontmatter(table_col: str, hint: str) -> str:
    table, col = table_col.split(".")
    tags = _COLUMN_TAGS.get(table_col, "[字段, 隐性知识]")
    related = _COLUMN_RELATED.get(table_col, [f"wiki/tables/{table}.md"])
    related_yaml = "\n".join(f"  - {r}" for r in related)
    return f"""---
title: "{table}.{col} 字段知识"
type: Column
resource: {table}.{col}
tags: {tags}
confidence: seed
related:
{related_yaml}
updated: {_DATE}
---

# {table}.{col} 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

"""


_COLUMN_TAGS = {
    "WIP_LOT.LOT_STS": "[字段, 隐性知识, 在制品, 编码]",
    "PRD_PRODUCT.TECH_NODE": "[字段, 隐性知识, 产品, 技术节点]",
    "EQP_EQUIPMENT.STATUS_CD": "[字段, 隐性知识, 设备, 状态]",
    "QCS_DEFECT.DEFECT_CD": "[字段, 隐性知识, 质量, 缺陷]",
    "QCS_DEFECT.DISPOSITION": "[字段, 隐性知识, 质量, 处置]",
    "YLD_DAILY.STAT_DT": "[字段, 隐性知识, 良率, 时间]",
    "YLD_DAILY.YLD_RATE": "[字段, 隐性知识, 良率, KPI]",
    "WIP_LOT_HIST.QTY_OUT": "[字段, 产出, 在制品]",
    "WIP_LOT_HIST.DEFECT_CNT": "[字段, 缺陷, 在制品]",
}

_COLUMN_RELATED = {
    "WIP_LOT.LOT_STS": ["wiki/tables/WIP_LOT.md", "wiki/metrics/hold-lot-count.md"],
    "PRD_PRODUCT.TECH_NODE": ["wiki/tables/PRD_PRODUCT.md"],
    "EQP_EQUIPMENT.STATUS_CD": ["wiki/tables/EQP_EQUIPMENT.md"],
    "QCS_DEFECT.DEFECT_CD": ["wiki/tables/QCS_DEFECT.md", "wiki/metrics/wafer-yield-rate.md"],
    "QCS_DEFECT.DISPOSITION": ["wiki/tables/QCS_DEFECT.md", "wiki/metrics/wafer-yield-rate.md"],
    "YLD_DAILY.STAT_DT": ["wiki/tables/YLD_DAILY.md", "wiki/metrics/wafer-yield-rate.md"],
    "YLD_DAILY.YLD_RATE": ["wiki/tables/YLD_DAILY.md", "wiki/metrics/wafer-yield-rate.md"],
    "WIP_LOT_HIST.QTY_OUT": ["wiki/tables/WIP_LOT_HIST.md"],
    "WIP_LOT_HIST.DEFECT_CNT": ["wiki/tables/WIP_LOT_HIST.md", "wiki/tables/QCS_DEFECT.md"],
}


def _column_md(table_col: str) -> str:
    """返回某个字段的 Mock 模板 markdown。"""
    hint = _COLUMN_WITH_TACIT.get(table_col, "通用字段知识")
    body = _COLUMN_MOCK_BODIES.get(table_col, f"""## 业务含义

{table_col} 字段的通用知识占位。

## Text2SQL 注意事项

无特殊注意事项。

## 血缘

- 所属表：见 related 字段
""")
    return _column_frontmatter(table_col, hint) + body


_SYSTEM_PROMPT = (
    "你是半导体晶圆厂数据资产知识库的专家编译器。根据给定的数据字典 JSON，"
    "按照 OKF 规范生成一份高质量的 Markdown 知识文件。必须包含 YAML frontmatter"
    "（type/title/resource/tags/confidence(取 llm-inferred)/updated）和正文章节："
    "业务含义 / 关键字段表格（含隐性知识列）/ 血缘 / Text2SQL 注意事项 / 来源。"
    "要写足隐性知识（货期编码、口径陷阱等）。只输出 .md 内容本身。"
)

_COLUMN_SYSTEM_PROMPT = (
    "你是半导体晶圆厂数据资产知识库的专家编译器。根据给定的字段信息和隐性知识提示，"
    "按照 OKF 规范为该字段生成一份高质量的 Markdown 知识文件。"
    "必须包含 YAML frontmatter："
    "type=Column / title / resource（格式 TABLE.COLUMN）/ tags / confidence=llm-inferred / updated / related（关联的表知识点路径）。"
    "正文必须包含：业务含义 / 编码对照或格式说明（隐性知识） / Text2SQL 注意事项 / 血缘。"
    "要重点突出隐性知识和 SQL 陷阱。只输出 .md 内容本身。"
)


def _table_json_to_md(table: str) -> str:
    """用真实 raw JSON 拼 user prompt，调 LLM 生成 markdown。"""
    raw = extractor.load_raw(table)
    hint = _TABLE_HINTS.get(table, "无额外隐性知识说明。")
    user = (
        f"请为表 {table} 生成知识文件。\n"
        f"隐性知识提示：{hint}\n\n"
        f"原始数据字典 JSON：\n{raw}"
    )
    md = chat_complete(_SYSTEM_PROMPT, user)
    if md is None:
        raise RuntimeError(f"LLM 不可用或失败，表 {table}")
    # 校验 & 清洗 LLM 输出
    cleaned = _validate_and_clean_md(md, expected_type="Table", resource=table)
    # 强制注入正确的 related 字段（保证血缘关系准确，不依赖 LLM 发挥）
    related = _RELATED_BY_TABLE.get(table, [])
    cleaned = _inject_related(cleaned, related)
    return cleaned


def _column_json_to_md(table_col: str) -> str:
    """用 raw JSON + 隐性知识提示，调 LLM 生成字段知识 markdown。"""
    table, col = table_col.split(".")
    raw = extractor.load_raw(table)
    # 从 raw 中找到该字段的信息
    col_info = next((c for c in raw.get("columns", []) if c["name"] == col), {})
    hint = _COLUMN_WITH_TACIT.get(table_col, "无额外隐性知识说明。")
    user = (
        f"请为字段 {table}.{col} 生成知识文件。\n"
        f"隐性知识提示：{hint}\n\n"
        f"字段信息：\n{col_info}\n\n"
        f"所属表完整字典：\n{raw}"
    )
    md = chat_complete(_COLUMN_SYSTEM_PROMPT, user)
    if md is None:
        raise RuntimeError(f"LLM 不可用或失败，字段 {table_col}")
    cleaned = _validate_and_clean_md(md, expected_type="Column", resource=table_col)
    # 强制注入正确的 related 字段
    related = _COLUMN_RELATED.get(table_col, [f"wiki/tables/{table}.md"])
    cleaned = _inject_related(cleaned, related)
    return cleaned


# --------------------------------------------------------------------------
# LLM 输出校验与清洗
# --------------------------------------------------------------------------
_VALID_TYPES = {"Table", "Column", "Metric", "Spec"}


def _validate_and_clean_md(md: str, expected_type: str, resource: str) -> str:
    """校验 LLM 输出的 markdown 是否符合 OKF 规范，必要时修复。

    校验项：
    - 必须有 YAML frontmatter
    - type 必须是合法枚举
    - 必须有 title / resource
    - confidence 设为 llm-inferred（覆盖 LLM 可能乱写的值）
    - 去除 markdown 代码块包裹（如果 LLM 不小心包了 ```markdown）
    """
    import re as _re

    text = md.strip()

    # 去除可能的代码块包裹
    if text.startswith("```"):
        text = _re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = _re.sub(r"\n```$", "", text)
        text = text.strip()

    # 确保有 frontmatter
    if not text.startswith("---"):
        # 尝试从正文提取第一个 --- 之前的内容
        pass

    # 解析 frontmatter（简单解析，不依赖外部库，避免循环依赖）
    parts = text.split("---", 2)
    if len(parts) < 3:
        # 没有 frontmatter，补一个
        text = (
            f"---\n"
            f"title: \"{resource} 知识\"\n"
            f"type: {expected_type}\n"
            f"resource: {resource}\n"
            f"tags: []\n"
            f"confidence: llm-inferred\n"
            f"updated: {_DATE}\n"
            f"---\n\n"
            f"# {resource}\n\n"
            f"{text}"
        )
        return text

    fm_text = parts[1].strip()
    body = parts[2].strip()

    # 简单解析 YAML frontmatter（逐行 key: value）
    fm: dict[str, str | list[str]] = {}
    current_key = None
    for line in fm_text.split("\n"):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
        # 列表项
        if line.startswith("  - ") or line.startswith("- "):
            if current_key and isinstance(fm.get(current_key), list):
                fm[current_key].append(line_stripped[2:].strip())
            continue
        # key: value
        if ":" in line_stripped:
            k, v = line_stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v == "":
                fm[k] = []
                current_key = k
            else:
                # 去除引号
                v = v.strip('"').strip("'")
                fm[k] = v
                current_key = k

    # 修复 type
    fm_type = str(fm.get("type", "")).strip()
    if fm_type not in _VALID_TYPES:
        fm["type"] = expected_type
    else:
        fm["type"] = fm_type

    # 修复 resource
    if not fm.get("resource"):
        fm["resource"] = resource

    # 修复 title
    if not fm.get("title"):
        fm["title"] = f"{resource} 知识"

    # 强制 confidence 为 llm-inferred
    fm["confidence"] = "llm-inferred"

    # 强制 updated
    fm["updated"] = _DATE

    # 确保 tags 是列表
    if "tags" not in fm or not isinstance(fm.get("tags"), list):
        fm["tags"] = [expected_type.lower()]

    # 重建 frontmatter
    fm_lines = ["---"]
    for k in ["title", "type", "resource", "tags", "confidence", "updated"]:
        v = fm.get(k, "")
        if k == "tags" and isinstance(v, list):
            fm_lines.append("tags:")
            for t in v:
                fm_lines.append(f"  - {t}")
        elif k == "related" and isinstance(v, list):
            fm_lines.append("related:")
            for r in v:
                fm_lines.append(f"  - {r}")
        elif isinstance(v, str):
            if k == "title":
                fm_lines.append(f'title: "{v}"')
            else:
                fm_lines.append(f"{k}: {v}")
    # related 字段
    if fm.get("related") and isinstance(fm["related"], list):
        fm_lines.append("related:")
        for r in fm["related"]:
            fm_lines.append(f"  - {r}")
    fm_lines.append("---")

    return "\n".join(fm_lines) + "\n\n" + body + "\n"


def _inject_related(md: str, related: list[str]) -> str:
    """向 markdown 的 frontmatter 中注入/覆盖 related 字段。

    用于确保 LLM 生成的知识文件也有正确的血缘关联关系。
    """
    if not related:
        return md
    parts = md.split("---", 2)
    if len(parts) < 3:
        return md
    fm_text = parts[1].strip()
    body = parts[2]

    # 移除已有的 related 字段
    import re as _re
    # 匹配 related: 及其后续的列表项（以 2 空格 - 开头的行）
    fm_text = _re.sub(
        r"related:\s*\n(?:\s+-\s+.*\n?)*",
        "",
        fm_text,
        flags=_re.MULTILINE,
    )
    fm_text = fm_text.strip()

    # 在 updated 之前插入 related
    related_block = "related:\n" + "\n".join(f"  - {r}" for r in related) + "\n"

    # 找 updated 行的位置，在它前面插入
    if "updated:" in fm_text:
        fm_text = fm_text.replace("updated:", related_block + "updated:", 1)
    else:
        fm_text = fm_text + "\n" + related_block + "updated: " + _DATE

    return "---\n" + fm_text + "\n---\n" + body


# --------------------------------------------------------------------------
# lineage 与 index 生成
# --------------------------------------------------------------------------
def _gen_lineage(table: str, conn) -> str:
    """依据 FK 元数据生成某表的 lineage markdown。"""
    fks = [f for f in db.get_meta_fk(conn) if f[1] == table]
    content = [f"---",
               "title: \"" + f"{table}__lineage 血缘\"",
               "type: Spec",
               "resource: " + f"{table}__lineage",
               "tags: [血缘, lineage]",
               "confidence: author",
               f"updated: {_DATE}",
               "---", "",
               f"# {table} 血缘", "",
               "## 上游（被谁引用 / 引用哪些主档）", ""]
    if fks:
        content.append("| 外键列 | 目标表 |")
        content.append("|--------|--------|")
        for _col, _src, tgt, _tc in fks:
            content.append(f"| {_col} | [{tgt}](../wiki/tables/{tgt}.md) |")
    else:
        content.append("_无外键（主档表）。_")
    # 语义下游（由相关表反查）
    downstream = [f[1] for f in db.get_meta_fk(conn) if f[2] == table]
    content += ["", "## 下游（引用本表的表）", ""]
    if downstream:
        for t in dict.fromkeys(downstream):
            content.append(f"- [{t}](../wiki/tables/{t}.md)")
    else:
        content.append("_无直接下游。_")
    return "\n".join(content) + "\n"


def _gen_index(tables: list[str], metrics: list[dict], columns: list[str]) -> str:
    """重建全局 index.md。"""
    lines = [
        "---",
        "title: FabWiki 知识包导航",
        "type: Spec",
        "resource: index",
        "tags: [导航, 首页]",
        "confidence: author",
        f"updated: {_DATE}",
        "---",
        "",
        "# FabWiki 知识包（OKF）",
        "",
        "> 本索引为全局导航入口，由 compiler 编译时自动刷新。",
        "",
        "## 📐 规范",
        "",
        "- [OKF 约定与知识规范](spec/conventions.md)",
        "- [Text2SQL 生成规则](spec/text2sql-rules.md)",
        "",
        "## 📊 表知识（Tables）",
        "",
    ]
    for t in tables:
        lines.append(f"- [{t}](../wiki/tables/{t}.md)「{t}」")
    lines += ["", "## 🔖 字段知识（Columns）", "",
              "> 含有隐性知识的关键字段，点击查看详细说明："]
    for c in sorted(columns):
        lines.append(f"- [{c}](../wiki/columns/{c}.md)")
    lines += ["", "## 📈 指标（Metrics）", ""]
    for m in metrics:
        lines.append(f"- [{m['title']}](../wiki/metrics/{m['resource']}.md)")
    lines += ["", "## 🩸 血缘", "", "> 每张表对应一个 lineage 文件："]
    for t in tables:
        lines.append(f"- [{t}__lineage](../wiki/lineage/{t}__lineage.md)")
    lines += ["", "", "---", f"_经 compiler 编译生成 · {_DATE}_"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def compile_all(force_llm: bool = False) -> dict:
    """编译全部 L2 知识。返回统计 dict。

    - 有 Key 且非 force_llm 时：逐表先尝试真实 LLM，失败/不可用自动落 Mock。
    - force_llm=True：强制走 LLM（无 Key 则全部落 Mock）。
    """
    config.ensure_dirs()
    conn = db.connect()
    tables = db.table_names()

    stats = {"tables": 0, "columns": 0, "metrics": 0, "llm": 0, "mock": 0, "lineage": 0}
    llm_ok = config.LLM_AVAILABLE and not force_llm

    # --- 表知识 ---
    for table in tables:
        rc = db.row_count(conn, table)
        used_llm = False
        md = None
        if llm_ok:
            try:
                md = _table_json_to_md(table)
                used_llm = True
            except Exception:
                md = None
        if md is None:
            md = _table_md(table, rc)
        (config.WIKI_TABLES_DIR / f"{table}.md").write_text(
            md, encoding="utf-8")
        stats["tables"] += 1
        stats["llm" if used_llm else "mock"] += 1

        # 生成 lineage
        lg = _gen_lineage(table, conn)
        (config.WIKI_LINEAGE_DIR / f"{table}__lineage.md").write_text(
            lg, encoding="utf-8")
        stats["lineage"] += 1

    # --- Column 级知识（仅含隐性知识的字段）---
    column_list = list(_COLUMN_WITH_TACIT.keys())
    for table_col in column_list:
        used_llm = False
        md = None
        if llm_ok:
            try:
                md = _column_json_to_md(table_col)
                used_llm = True
            except Exception:
                md = None
        if md is None:
            md = _column_md(table_col)
        (config.WIKI_COLUMNS_DIR / f"{table_col}.md").write_text(
            md, encoding="utf-8")
        stats["columns"] += 1
        stats["llm" if used_llm else "mock"] += 1

    # --- 指标 ---
    for m in METRICS:
        (config.WIKI_METRICS_DIR / f"{m['resource']}.md").write_text(
            _metric_md(m), encoding="utf-8")
        stats["metrics"] += 1

    # --- 刷新 index ---
    (config.INDEX_MD).write_text(_gen_index(tables, METRICS, column_list), encoding="utf-8")
    conn.close()
    return stats
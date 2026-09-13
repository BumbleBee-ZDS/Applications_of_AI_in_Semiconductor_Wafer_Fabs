---
title: OKF 约定与知识规范
type: Spec
resource: conventions
tags: [规范, OKF, 元数据]
confidence: author
related: [spec/text2sql-rules.md, index.md]
updated: 2026-09-13
---

# OKF 约定与知识规范

FabWiki 基于 OKF（Open Knowledge Format）思想：**一个知识包 = 一个文件夹，
一个知识点 = 一个 Markdown 文件（YAML frontmatter + 正文），文件间用相对路径
链接构成知识图谱。**

## 1. type 枚举

| type     | 含义                              | 存放目录                 |
|----------|-----------------------------------|--------------------------|
| `Table`  | 数据库表的知识点                    | `wiki/tables/`           |
| `Column` | 字段级知识点（仅含隐性知识的字段） | `wiki/columns/`          |
| `Metric` | 业务指标（可复用的计算口径）        | `wiki/metrics/`          |
| `Spec`   | 规范 / 规则文档                    | `spec/`                  |

## 2. YAML frontmatter 必含字段

- `title`: 知识点标题（人类可读）
- `type`: 见上表枚举
- `resource`: 唯一标识。Table 用表名（如 `WIP_LOT`）；Column 用 `表名.字段名`；
  Metric 用指标英文名
- `tags`: 标签数组（工艺组、域、业务口径等）
- `confidence`: 置信度，见第 4 节
- `updated`: 更新时间 `YYYY-MM-DD`
- `related`: 可选，关联知识点的相对路径（knowledge/ 根目录视角）

## 3. 链接规则

- 正文用 Markdown 相对路径链接：`[WIP_LOT](../wiki/tables/WIP_LOT.md)`
- 链接相对当前文件所在目录解析，最终归一化到 knowledge/ 根目录
- 编译器依据 `related` 字段写入表间上下游关系，Text2SQL 据此导航血缘

## 4. confidence 定义

| 取值          | 含义                                         |
|---------------|----------------------------------------------|
| `author`      | 人工编写/规范文档，可信度最高                 |
| `llm-inferred`| LLM 根据 raw 数据字典推断，需人工复核         |
| `verified`    | 已经过人工评审并核对                             |
| `seed`        | 由 Mock seed 模板写入（离线演示基线）          |

> 首页统计页会展示 confidence 分布，`llm-inferred` 占比高时提示需要人工复核。

## 5. 隐性知识必须显式记录

数据字典里"看着没意义、实际有深意"的字段编码（如 `LOT_STS='99'` 表示测试批次、
`DEFECT_CD` 前缀规则）必须写入 L2 知识文档的「隐性知识 / 编码对照」章节，
Text2SQL 靠这些说明避开查询陷阱。
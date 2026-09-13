---
title: "QCS_DEFECT 表知识"
type: Table
resource: QCS_DEFECT
tags: [质量, 缺陷]
confidence: seed
related:
  - wiki/tables/WIP_LOT.md
  - wiki/tables/ENG_STEP.md
  - wiki/metrics/yield-rate.md
  - wiki/columns/QCS_DEFECT.DEFECT_CD.md
  - wiki/columns/QCS_DEFECT.DISPOSITION.md
updated: 2026-09-13
---

# QCS_DEFECT 表

> L2 编译产物（Mock seed 基线）· 当前约 114 行

## 业务含义

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

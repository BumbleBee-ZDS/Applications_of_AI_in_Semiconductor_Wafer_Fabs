---
title: "ENG_STEP 表知识"
type: Table
resource: ENG_STEP
tags: [工程, 工序]
confidence: seed
related:
  - wiki/tables/WIP_LOT_HIST.md
  - wiki/tables/QCS_DEFECT.md
  - wiki/tables/PRD_ROUTE.md
updated: 2026-09-13
---

# ENG_STEP 表

> L2 编译产物（Mock seed 基线）· 当前约 9 行

## 业务含义

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

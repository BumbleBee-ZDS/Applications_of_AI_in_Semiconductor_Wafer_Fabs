---
title: "PRD_ROUTE 表知识"
type: Table
resource: PRD_ROUTE
tags: [产品, 工艺路线]
confidence: seed
related:
  - wiki/tables/PRD_PRODUCT.md
  - wiki/tables/ENG_STEP.md
updated: 2026-09-13
---

# PRD_ROUTE 表

> L2 编译产物（Mock seed 基线）· 当前约 15 行

## 业务含义

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

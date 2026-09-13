---
title: "PRD_PRODUCT 表知识"
type: Table
resource: PRD_PRODUCT
tags: [产品, 主档]
confidence: seed
related:
  - wiki/tables/WIP_LOT.md
  - wiki/tables/YLD_DAILY.md
  - spec/text2sql-rules.md
  - wiki/columns/PRD_PRODUCT.TECH_NODE.md
updated: 2026-09-13
---

# PRD_PRODUCT 表

> L2 编译产物（Mock seed 基线）· 当前约 5 行

## 业务含义

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

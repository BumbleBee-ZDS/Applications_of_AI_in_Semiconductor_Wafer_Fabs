---
title: "PRD_PRODUCT.TECH_NODE 字段知识"
type: Column
resource: PRD_PRODUCT.TECH_NODE
tags: [字段, 隐性知识, 产品, 技术节点]
confidence: seed
related:
  - wiki/tables/PRD_PRODUCT.md
updated: 2026-09-13
---

# PRD_PRODUCT.TECH_NODE 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

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

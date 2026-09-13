---
title: "QCS_DEFECT.DEFECT_CD 字段知识"
type: Column
resource: QCS_DEFECT.DEFECT_CD
tags: [字段, 隐性知识, 质量, 缺陷]
confidence: seed
related:
  - wiki/tables/QCS_DEFECT.md
  - wiki/metrics/wafer-yield-rate.md
updated: 2026-09-13
---

# QCS_DEFECT.DEFECT_CD 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

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

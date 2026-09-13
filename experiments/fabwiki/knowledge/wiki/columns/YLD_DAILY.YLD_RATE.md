---
title: "YLD_DAILY.YLD_RATE 字段知识"
type: Column
resource: YLD_DAILY.YLD_RATE
tags: [字段, 隐性知识, 良率, KPI]
confidence: seed
related:
  - wiki/tables/YLD_DAILY.md
  - wiki/metrics/wafer-yield-rate.md
updated: 2026-09-13
---

# YLD_DAILY.YLD_RATE 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

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

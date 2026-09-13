---
title: "YLD_DAILY.STAT_DT 字段知识"
type: Column
resource: YLD_DAILY.STAT_DT
tags: [字段, 隐性知识, 良率, 时间]
confidence: seed
related:
  - wiki/tables/YLD_DAILY.md
  - wiki/metrics/wafer-yield-rate.md
updated: 2026-09-13
---

# YLD_DAILY.STAT_DT 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

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

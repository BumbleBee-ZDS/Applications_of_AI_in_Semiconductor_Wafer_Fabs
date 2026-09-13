---
title: "YLD_DAILY 表知识"
type: Table
resource: YLD_DAILY
tags: [良率, 日汇总]
confidence: seed
related:
  - wiki/tables/WIP_LOT_HIST.md
  - wiki/tables/PRD_PRODUCT.md
  - wiki/metrics/yield-rate.md
  - wiki/columns/YLD_DAILY.STAT_DT.md
  - wiki/columns/YLD_DAILY.YLD_RATE.md
updated: 2026-09-13
---

# YLD_DAILY 表

> L2 编译产物（Mock seed 基线）· 当前约 450 行

## 业务含义

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

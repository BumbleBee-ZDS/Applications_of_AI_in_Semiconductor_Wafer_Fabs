---
title: "WIP_LOT_HIST.DEFECT_CNT 字段知识"
type: Column
resource: WIP_LOT_HIST.DEFECT_CNT
tags: [字段, 缺陷, 在制品]
confidence: seed
related:
  - wiki/tables/WIP_LOT_HIST.md
  - wiki/tables/QCS_DEFECT.md
updated: 2026-09-13
---

# WIP_LOT_HIST.DEFECT_CNT 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

本步（某批次在某工序）检测出的缺陷总数。

## 口径说明

- 为本步的缺陷计数，不是累计缺陷数。
- 缺陷数量异常高时需排查工艺或设备问题。

## Text2SQL 注意事项

- 统计某工序总缺陷用 `SUM(DEFECT_CNT)`。
- 缺陷 Top N 查询：按 `STEP_ID` 或 `DEFECT_CD` 聚合后排序。
- 结合 `QCS_DEFECT` 表可查更详细的缺陷分类。

## 血缘

- 所属表：[WIP_LOT_HIST](../tables/WIP_LOT_HIST.md)

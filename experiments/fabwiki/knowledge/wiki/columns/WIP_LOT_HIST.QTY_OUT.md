---
title: "WIP_LOT_HIST.QTY_OUT 字段知识"
type: Column
resource: WIP_LOT_HIST.QTY_OUT
tags: [字段, 产出, 在制品]
confidence: seed
related:
  - wiki/tables/WIP_LOT_HIST.md
updated: 2026-09-13
---

# WIP_LOT_HIST.QTY_OUT 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

本步（某批次在某工序）产出的晶圆数量。

## 口径说明

- 为过站（Track Out）时的实际产出数。
- 可能小于投入数（因为有报废、缺陷等）。

## Text2SQL 注意事项

- 统计某设备/工序的总产出用 `SUM(QTY_OUT)`。
- 按时间段过滤用 `TRACK_OUT_DT`。
- 按设备统计用 `GROUP BY EQP_ID`。

## 血缘

- 所属表：[WIP_LOT_HIST](../tables/WIP_LOT_HIST.md)

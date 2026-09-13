---
title: "WIP_LOT_HIST 表知识"
type: Table
resource: WIP_LOT_HIST
tags: [wip, 过站, fab]
confidence: seed
related:
  - wiki/tables/WIP_LOT.md
  - wiki/tables/ENG_STEP.md
  - wiki/tables/EQP_EQUIPMENT.md
  - wiki/tables/YLD_DAILY.md
  - wiki/columns/WIP_LOT_HIST.QTY_OUT.md
  - wiki/columns/WIP_LOT_HIST.DEFECT_CNT.md
updated: 2026-09-13
---

# WIP_LOT_HIST 表

> L2 编译产物（Mock seed 基线）· 当前约 876 行

## 业务含义

批次过站历史：批次在每一道工序制造时的记录（何时、在哪台设备、产出多少、本步缺陷数）。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| HIST_ID | INTEGER | 历史流水号（PK） | |
| LOT_ID | TEXT | 批次号，FK→WIP_LOT | |
| STEP_ID | TEXT | 工序，FK→ENG_STEP | |
| EQP_ID | TEXT | 设备，FK→EQP_EQUIPMENT | |
| TRACK_OUT_DT | TEXT | 过站（Track Out）时间 | |
| QTY_OUT | INTEGER | 本步产出晶圆数 | |
| DEFECT_CNT | INTEGER | 本步缺陷数 | 异常高需排查 |

## 血缘

- 上游：批次 [WIP_LOT](../wiki/tables/WIP_LOT.md)、工序 [ENG_STEP](../wiki/tables/ENG_STEP.md)、设备 [EQP_EQUIPMENT](../wiki/tables/EQP_EQUIPMENT.md)
- 下游：日良率汇总 [YLD_DAILY](../wiki/tables/YLD_DAILY.md)（由加工数据汇聚而来）

## Text2SQL 注意事项

- 统计设备产出/缺陷按下游聚合 `EQP_ID`、`STEP_ID` 时用 `SUM(QTY_OUT)`。
- 时段过滤用 `TRACK_OUT_DT`。

## 来源

L1 数据字典 `raw/dictionary/WIP_LOT_HIST.json`（Mock seed 基线）。

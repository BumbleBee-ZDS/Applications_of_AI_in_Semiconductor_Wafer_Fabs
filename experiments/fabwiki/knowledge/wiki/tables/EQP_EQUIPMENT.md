---
title: "EQP_EQUIPMENT 表知识"
type: Table
resource: EQP_EQUIPMENT
tags: [设备, 主档]
confidence: seed
related:
  - wiki/tables/WIP_LOT_HIST.md
  - wiki/columns/EQP_EQUIPMENT.STATUS_CD.md
updated: 2026-09-13
---

# EQP_EQUIPMENT 表

> L2 编译产物（Mock seed 基线）· 当前约 10 行

## 业务含义

设备主档，定义晶圆厂所有生产设备的类型与当前状态。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| EQP_ID | TEXT | 设备号（PK） | |
| EQP_NM | TEXT | 设备名 | |
| EQP_TYPE | TEXT | 设备类型 | 如 LITHO / ETCH |
| TOOL_GRP | TEXT | 工具组 | 对应工艺组 |
| STATUS_CD | TEXT | 状态编码 | **M=PM保养中(算可用产能)** |

### STATUS_CD 编码对照（隐性知识）

| 编码 | 含义 | 备注 |
|------|------|------|
| R | Run | 运行中 |
| I | Idle | 空闲 |
| D | Down | 故障停机 |
| **M** | PM 保养中 | **统计可用产能时计入** |

## 血缘

- 上游：被 [WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md) 引用。

## Text2SQL 注意事项

- 算"可用产能/可用设备数"时用 `STATUS_CD IN ('R','I','M')`，其中 M 也算。

## 来源

L1 数据字典 `raw/dictionary/EQP_EQUIPMENT.json`（Mock seed 基线）。

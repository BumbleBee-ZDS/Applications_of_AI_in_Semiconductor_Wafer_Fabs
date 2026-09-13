---
title: "EQP_EQUIPMENT.STATUS_CD 字段知识"
type: Column
resource: EQP_EQUIPMENT.STATUS_CD
tags: [字段, 隐性知识, 设备, 状态]
confidence: seed
related:
  - wiki/tables/EQP_EQUIPMENT.md
updated: 2026-09-13
---

# EQP_EQUIPMENT.STATUS_CD 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

设备当前状态编码，反映设备的可用情况。

## 编码对照（隐性知识）

| 编码 | 含义 | 是否计入可用产能 |
|------|------|-----------------|
| R | Run（运行中） | ✅ 是 |
| I | Idle（空闲） | ✅ 是 |
| D | Down（故障停机） | ❌ 否 |
| **M** | PM 保养中 | **✅ 是**（保养是计划性的，不算故障停机） |

## Text2SQL 注意事项

- 统计可用设备数：`WHERE STATUS_CD IN ('R', 'I', 'M')`。
- 注意 **M（PM 保养中）也要算可用产能**，不要只查 R 和 I。
- 统计故障设备：`WHERE STATUS_CD = 'D'`。

## 血缘

- 所属表：[EQP_EQUIPMENT](../tables/EQP_EQUIPMENT.md)

---
title: "WIP_LOT.LOT_STS 字段知识"
type: Column
resource: WIP_LOT.LOT_STS
tags: [字段, 隐性知识, 在制品, 编码]
confidence: seed
related:
  - wiki/tables/WIP_LOT.md
  - wiki/metrics/hold-lot-count.md
updated: 2026-09-13
---

# WIP_LOT.LOT_STS 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

批次状态编码，标识晶圆批次当前所处的生命周期阶段。

## 编码对照（隐性知识）

| 编码 | 含义 | 说明 |
|------|------|------|
| 01 | Released | 已释放，等待投片 |
| 03 | Running | 生产中，正在某工序加工 |
| 05 | Hold | 待 MRB 评审，暂停生产 |
| 07 | Terminated | 已终止，不再继续生产 |
| **99** | 测试批次 | **任何统计查询必须排除 `LOT_STS='99'`** |

## Text2SQL 注意事项

- 统计在制品数量、良率、Hold 批次等，**必须**加上 `WHERE LOT_STS <> '99'` 排除测试批次。
- 查 Hold 批次用 `LOT_STS = '05'`，同时仍要排除 `99`。
- 不要只按字面意思查 `LOT_STS = 'Hold'`，存储值是编码数字。

## 血缘

- 所属表：[WIP_LOT](../tables/WIP_LOT.md)
- 相关指标：[Hold 批次数量](../../metrics/hold-lot-count.md)

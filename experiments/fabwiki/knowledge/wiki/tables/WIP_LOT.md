---
title: "WIP_LOT 表知识"
type: Table
resource: WIP_LOT
tags: [wip, 在制品, fab]
confidence: seed
related:
  - wiki/tables/WIP_LOT_HIST.md
  - wiki/tables/QCS_DEFECT.md
  - wiki/tables/PRD_PRODUCT.md
  - wiki/columns/WIP_LOT.LOT_STS.md
updated: 2026-09-13
---

# WIP_LOT 表

> L2 编译产物（Mock seed 基线）· 当前约 225 行

## 业务含义

在制品（WIP）批次主档，记录晶圆厂当前在制的每一批次。

## 关键字段

| 字段 | 类型 | 说明 | 隐性知识 |
|------|------|------|----------|
| LOT_ID | TEXT | 批次号（PK） | |
| PRODUCT_ID | TEXT | 产品号，关联 PRD_PRODUCT | |
| STAGE_CD | TEXT | 当前工序 | |
| LOT_STS | TEXT | 批次状态 | **05=Hold(待MRB评审)；99=测试批次，统计必须排除** |
| QTY_IN | INTEGER | 投入晶圆数 | |
| WAFER_CNT | INTEGER | 批次晶圆数 | |
| CREATE_DT | TEXT | 建批时间 | |
| LAST_MOD_DT | TEXT | 最后修改时间 | |

### LOT_STS 编码对照（隐性知识）

| 编码 | 含义 | 说明 |
|------|------|------|
| 01 | Released | 已释放 |
| 03 | Running | 生产中 |
| 05 | Hold | 待 MRB 评审 |
| 07 | Terminated | 终止 |
| **99** | 测试批次 | **任何统计查询必须排除 `LOT_STS='99'`** |

## 血缘

- 下游：批次过站历史 [WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md)、
  缺陷 [QCS_DEFECT](../wiki/tables/QCS_DEFECT.md)
- 上游：产品主档 [PRD_PRODUCT](../wiki/tables/PRD_PRODUCT.md)

## Text2SQL 注意事项

- 统计在制品数量/良率时必须排除测试批次：`WHERE LOT_STS <> '99'`。
- 查 Hold 批次用 `LOT_STS='05'`，同时仍要排除 `99`。

## 来源

L1 数据字典 `raw/dictionary/WIP_LOT.json`（Mock seed 基线）。

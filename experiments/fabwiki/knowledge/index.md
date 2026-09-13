---
title: FabWiki 知识包导航
type: Spec
resource: index
tags: [导航, 首页]
confidence: author
updated: 2026-09-13
---

# FabWiki 知识包（OKF）

> 本索引为全局导航入口，由 compiler 编译时自动刷新。

## 📐 规范

- [OKF 约定与知识规范](spec/conventions.md)
- [Text2SQL 生成规则](spec/text2sql-rules.md)

## 📊 表知识（Tables）

- [WIP_LOT](../wiki/tables/WIP_LOT.md)「WIP_LOT」
- [WIP_LOT_HIST](../wiki/tables/WIP_LOT_HIST.md)「WIP_LOT_HIST」
- [PRD_PRODUCT](../wiki/tables/PRD_PRODUCT.md)「PRD_PRODUCT」
- [PRD_ROUTE](../wiki/tables/PRD_ROUTE.md)「PRD_ROUTE」
- [ENG_STEP](../wiki/tables/ENG_STEP.md)「ENG_STEP」
- [EQP_EQUIPMENT](../wiki/tables/EQP_EQUIPMENT.md)「EQP_EQUIPMENT」
- [QCS_DEFECT](../wiki/tables/QCS_DEFECT.md)「QCS_DEFECT」
- [YLD_DAILY](../wiki/tables/YLD_DAILY.md)「YLD_DAILY」

## 🔖 字段知识（Columns）

> 含有隐性知识的关键字段，点击查看详细说明：
- [EQP_EQUIPMENT.STATUS_CD](../wiki/columns/EQP_EQUIPMENT.STATUS_CD.md)
- [PRD_PRODUCT.TECH_NODE](../wiki/columns/PRD_PRODUCT.TECH_NODE.md)
- [QCS_DEFECT.DEFECT_CD](../wiki/columns/QCS_DEFECT.DEFECT_CD.md)
- [QCS_DEFECT.DISPOSITION](../wiki/columns/QCS_DEFECT.DISPOSITION.md)
- [WIP_LOT.LOT_STS](../wiki/columns/WIP_LOT.LOT_STS.md)
- [WIP_LOT_HIST.DEFECT_CNT](../wiki/columns/WIP_LOT_HIST.DEFECT_CNT.md)
- [WIP_LOT_HIST.QTY_OUT](../wiki/columns/WIP_LOT_HIST.QTY_OUT.md)
- [YLD_DAILY.STAT_DT](../wiki/columns/YLD_DAILY.STAT_DT.md)
- [YLD_DAILY.YLD_RATE](../wiki/columns/YLD_DAILY.YLD_RATE.md)

## 📈 指标（Metrics）

- [晶圆良率](../wiki/metrics/wafer-yield-rate.md)
- [Hold 批次数量](../wiki/metrics/hold-lot-count.md)

## 🩸 血缘

> 每张表对应一个 lineage 文件：
- [WIP_LOT__lineage](../wiki/lineage/WIP_LOT__lineage.md)
- [WIP_LOT_HIST__lineage](../wiki/lineage/WIP_LOT_HIST__lineage.md)
- [PRD_PRODUCT__lineage](../wiki/lineage/PRD_PRODUCT__lineage.md)
- [PRD_ROUTE__lineage](../wiki/lineage/PRD_ROUTE__lineage.md)
- [ENG_STEP__lineage](../wiki/lineage/ENG_STEP__lineage.md)
- [EQP_EQUIPMENT__lineage](../wiki/lineage/EQP_EQUIPMENT__lineage.md)
- [QCS_DEFECT__lineage](../wiki/lineage/QCS_DEFECT__lineage.md)
- [YLD_DAILY__lineage](../wiki/lineage/YLD_DAILY__lineage.md)


---
_经 compiler 编译生成 · 2026-09-13_

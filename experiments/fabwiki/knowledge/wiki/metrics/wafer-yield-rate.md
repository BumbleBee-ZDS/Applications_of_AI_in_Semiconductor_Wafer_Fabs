---
title: "晶圆良率"
type: Metric
resource: wafer-yield-rate
tags: [良率, KPI]
confidence: seed
related:
  - wiki/tables/YLD_DAILY.md
  - wiki/tables/QCS_DEFECT.md
  - wiki/tables/PRD_PRODUCT.md
updated: 2026-09-13
---

# 晶圆良率

> L2 编译产物（指标口径）· Mock seed 基线
## 业务含义

产品在某工艺组（或全厂）的晶圆良率，衡量产出质量的核心 KPI。

## 计算口径

```
良率 = OUTPUT_WAFER / INPUT_WAFER
```
直接取 [YLD_DAILY](../wiki/tables/YLD_DAILY.md) 的 `YLD_RATE` 字段即可，已被 _PKG_YLD_CALC_ 汇总好。

## 隐性知识 / 陷阱

- **排除测试批次**：任何良率统计必须排除 `WIP_LOT.LOT_STS='99'`。
- **排除 Scrap**：产出侧已排除 `QCS_DEFECT.DISPOSITION='SC'` 的晶圆。
- **TECH_NODE 需 CAST**：按技术节点维度对比时用
  `CAST(REPLACE(TECH_NODE,'nm','') AS INTEGER)`。
- **夜间 job 空窗**：`YLD_DAILY` 为夜间生成，当日 08:00 前查昨日可能为空。

## 血缘

- 依赖 [YLD_DAILY](../wiki/tables/YLD_DAILY.md)；口径涉及 [QCS_DEFECT](../wiki/tables/QCS_DEFECT.md)。

## Text2SQL 注意事项

- 趋势查询：`SELECT stat_dt, product_id, AVG(yld_rate) FROM YLD_DAILY ... GROUP BY ...`。
- 较小样本用 `AVG(YLD_RATE)` 而非对行数取平均。


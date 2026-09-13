---
title: "Hold 批次数量"
type: Metric
resource: hold-lot-count
tags: [在制品, KPI, MRB]
confidence: seed
related:
  - wiki/tables/WIP_LOT.md
updated: 2026-09-13
---

# Hold 批次数量

> L2 编译产物（指标口径）· Mock seed 基线
## 业务含义

当前处于 Hold（待 MRB 评审）状态的批次数量，反映在制品风险水位。

## 计算口径

```sql
SELECT COUNT(*) FROM WIP_LOT
WHERE LOT_STS = '05'
  AND LOT_STS <> '99';
```

## 隐性知识 / 陷阱

- **LOT_STS='05' = Hold**，待 MRB 评审。
- **必须排除 '99' 测试批次**，否则把测试数据算进风险批次。
- 如需按产品/工序细分，GROUP BY PRODUCT_ID / STAGE_CD。

## 血缘

- 依赖 [WIP_LOT](../wiki/tables/WIP_LOT.md)。

## Text2SQL 注意事项

- 一定带 `LOT_STS <> '99'` 过滤（规则见 [text2sql-rules](../spec/text2sql-rules.md)）。


---
title: "QCS_DEFECT.DISPOSITION 字段知识"
type: Column
resource: QCS_DEFECT.DISPOSITION
tags: [字段, 隐性知识, 质量, 处置]
confidence: seed
related:
  - wiki/tables/QCS_DEFECT.md
  - wiki/metrics/wafer-yield-rate.md
updated: 2026-09-13
---

# QCS_DEFECT.DISPOSITION 字段

> L2 编译产物（Mock seed 基线）· 含隐性知识

## 业务含义

缺陷处置结论，表示发现缺陷后晶圆的最终处理方式。

## 编码对照（隐性知识）

| 编码 | 含义 | 是否计入产出 |
|------|------|-------------|
| OK | 正常通过 | ✅ 是 |
| RS | Rework（返工） | ✅ 是（返工后重新入线） |
| **SC** | Scrap（报废） | **❌ 否**（报废晶圆不计入产出） |

## Text2SQL 注意事项

- 计算产出/良率时排除报废：`WHERE DISPOSITION <> 'SC'`。
- `YLD_DAILY` 表的 `OUTPUT_WAFER` 已经排除了 SC，直接用即可。
- 统计报废率：`SUM(CASE WHEN DISPOSITION='SC' THEN DEFECT_CNT ELSE 0 END) / SUM(DEFECT_CNT)`。

## 血缘

- 所属表：[QCS_DEFECT](../tables/QCS_DEFECT.md)
- 相关指标：[晶圆良率](../../metrics/wafer-yield-rate.md)

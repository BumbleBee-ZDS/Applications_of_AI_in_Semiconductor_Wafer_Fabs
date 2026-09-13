---
title: Text2SQL 生成规则（含 few-shot）
type: Spec
resource: text2sql-rules
tags: [Text2SQL, SQL, 规则]
confidence: author
related: [spec/conventions.md, index.md]
updated: 2026-09-13
---

# Text2SQL 生成规则

LLM 生成 SQL 时必须遵守以下规则。**这些规则与知识文件正文同等重要**，
text2sql 每次都随知识文件全文一起注入 prompt。

## 0. 总体原则

- 只用知识文档中出现的表 / 字段；不臆造不存在的列。
- 目标库为 SQLite，SQL 用标准（ANSI）写法，注意 SQLite 语法差异。
- **所有统计查询必须排除 `LOT_STS='99'`（测试批次）**，除非用户明确要求测试批次。
- 过滤条件中涉及字符串编码字段（如 `LOT_STS`、`DEFECT_CD`）、技术节点（`TECH_NODE`）
  时，按其真实存储值精确匹配。

## 1. 必读隐性知识清单（生成时对照）

| 表 / 字段          | 陷阱                                                            | 正确写法                                                   |
|--------------------|-----------------------------------------------------------------|------------------------------------------------------------|
| `WIP_LOT.LOT_STS`  | `05`=Hold（待 MRB），`99`=测试批次                                 | 查 Hold：`LOT_STS='05' AND LOT_STS<>'99'`（并排除 99）       |
| `QCS_DEFECT.DEFECT_CD` | 前缀 `P`=Particle, `S`=Scratch, `M`=Metal残留                  | `DEFECT_CD LIKE 'P%'`；不要按精确全码匹配                     |
| `QCS_DEFECT.DISPOSITION` | `SC`（Scrap）的晶圆不计入产出                                 | 算产出时过滤 `DISPOSITION<>'SC'`                              |
| `YLD_DAILY`        | 夜间 job 产物，当日 08:00 前昨日数据可能为空                       | 查"昨日"良率时用 `STAT_DT >= date('now','-1 day')` 之前的天尽量避开今日空值 |
| `PRD_PRODUCT.TECH_NODE` | 存字符串 `'28nm'`，数值比较需 CAST                              | `CAST(REPLACE(TECH_NODE,'nm','') AS INTEGER)` 再比较          |
| `EQP_EQUIPMENT.STATUS_CD` | `M`=PM 保养中（算可用产能）                                  | 算可用产能时 `STATUS_CD IN ('R','I','M')`                      |

## 2. 常用口径

- **晶圆良率**：`OUTPUT_WAFER / INPUT_WAFER`（YLD_DAILY 已含 `YLD_RATE`，直接用即可）。
- **Hold 批次数量**：`COUNT(*)` 于 `WIP_LOT` 且 `LOT_STS='05'`，排除 `'99'`。
- **缺陷 TopN**：按 `STEP_ID` 或 `DEFECT_CD` 聚合 `SUM(DEFECT_CNT)` 排序。

## 3. few-shot 样例

### 例 1：当前 Hold 中的批次数量
```sql
SELECT LOT_ID, PRODUCT_ID
FROM WIP_LOT
WHERE LOT_STS = '05'
  AND LOT_STS <> '99'
ORDER BY LAST_MOD_DT DESC;
```

### 例 2：最近一个月各产品良率趋势
```sql
SELECT STAT_DT, PRODUCT_ID, AVG(YLD_RATE) AS AVG_YLD
FROM YLD_DAILY
WHERE STAT_DT >= date('now', '-1 month')
GROUP BY STAT_DT, PRODUCT_ID
ORDER BY STAT_DT;
```

### 例 3：PHOTO 工序缺陷 Top10
```sql
SELECT S.STEP_NM, SUM(D.DEFECT_CNT) AS TOTAL_DEFECT
FROM QCS_DEFECT D
JOIN ENG_STEP S ON D.STEP_ID = S.STEP_ID
WHERE S.STEP_GRP = 'PHOTO'
GROUP BY S.STEP_NM
ORDER BY TOTAL_DEFECT DESC
LIMIT 10;
```

### 例 4：TECH_NODE=28nm 的产品及在制 Hold 批次
```sql
SELECT P.PRODUCT_NM, P.TECH_NODE, COUNT(W.LOT_ID) AS HOLD_LOTS
FROM PRD_PRODUCT P
LEFT JOIN WIP_LOT W
  ON P.PRODUCT_ID = W.PRODUCT_ID
 AND W.LOT_STS = '05' AND W.LOT_STS <> '99'
WHERE CAST(REPLACE(P.TECH_NODE, 'nm', '') AS INTEGER) = 28
GROUP BY P.PRODUCT_NM, P.TECH_NODE;
```

## 4. 输出格式

只返回一条纯净的 SQL 语句，**不要**用 markdown 代码块包裹（由调用方处理展示），
不解释、不加分号结尾（SQLite 兼容可留）。

## 5. 失败重试

执行报错时，系统会把错误信息回填给 LLM，要求其"修正 SQL 并重出"，最多重试 1 次。
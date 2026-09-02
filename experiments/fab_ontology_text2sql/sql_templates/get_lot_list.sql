-- 动力层模板: get_lot_list —— 批次列表（最近优先）
-- 参数: 无
SELECT LOT_ID        AS "批次号",
       PRODUCT_ID    AS "产品",
       CUSTOMER      AS "客户",
       LOT_QTY       AS "晶圆数",
       STATUS        AS "状态",
       CURRENT_STAGE AS "当前工序",
       START_TIME    AS "开始时间",
       FINISH_TIME   AS "完成时间"
FROM LOT_INFO
ORDER BY START_TIME DESC
LIMIT 50;
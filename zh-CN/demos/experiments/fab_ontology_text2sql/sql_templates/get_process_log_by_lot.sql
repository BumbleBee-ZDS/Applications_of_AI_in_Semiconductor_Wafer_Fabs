-- 动力层模板: get_process_log_by_lot —— 指定批次的完整工艺日志
-- 参数: (lot_id)
SELECT LOG_ID       AS "日志ID",
       LOT_ID       AS "批次号",
       EQP_ID       AS "设备编号",
       PROCESS_STEP AS "工序",
       RECIPE_ID    AS "配方",
       STATUS       AS "状态",
       START_TIME   AS "开始时间",
       END_TIME     AS "结束时间",
       PARAMETER    AS "工艺参数"
FROM PROCESS_LOG
WHERE LOT_ID = ?
ORDER BY START_TIME;
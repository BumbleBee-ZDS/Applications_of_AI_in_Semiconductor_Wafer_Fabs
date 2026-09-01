-- 动力层模板: get_yield_trend —— 良率趋势（按日聚合）
-- 参数: (start_time, end_time, eqp_id | NULL = 全部设备)
SELECT DATE(MEASURE_TIME)             AS "日期",
       ROUND(AVG(YIELD_RATE) * 100, 2) AS "平均良率(%)",
       COUNT(*)                        AS "晶圆数"
FROM WAFER_METROLOGY
WHERE MEASURE_TIME BETWEEN ? AND ?
  AND EQP_ID = COALESCE(?, EQP_ID)
GROUP BY DATE(MEASURE_TIME)
ORDER BY "日期";
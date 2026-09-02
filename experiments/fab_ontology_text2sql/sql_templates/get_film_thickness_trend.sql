-- 动力层模板: get_film_thickness_trend —— 膜厚趋势（按日聚合）
-- 参数: (start_time, end_time, eqp_id | NULL = 全部设备)
SELECT DATE(MEASURE_TIME)          AS "日期",
       ROUND(AVG(FILM_THICKNESS), 1) AS "平均膜厚",
       COUNT(*)                    AS "量测点数"
FROM WAFER_METROLOGY
WHERE MEASURE_TIME BETWEEN ? AND ?
  AND EQP_ID = COALESCE(?, EQP_ID)
GROUP BY DATE(MEASURE_TIME)
ORDER BY "日期";
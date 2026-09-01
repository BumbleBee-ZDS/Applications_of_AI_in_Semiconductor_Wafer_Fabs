-- 动力层模板: get_film_stats —— 膜厚统计（按设备）
-- 参数: (start_time, end_time, eqp_id | NULL = 全部设备)
SELECT EQP_ID            AS "设备编号",
       COUNT(*)          AS "量测点数",
       ROUND(AVG(FILM_THICKNESS), 1) AS "平均膜厚",
       MIN(FILM_THICKNESS) AS "最小膜厚",
       MAX(FILM_THICKNESS) AS "最大膜厚"
FROM WAFER_METROLOGY
WHERE MEASURE_TIME BETWEEN ? AND ?
  AND EQP_ID = COALESCE(?, EQP_ID)
GROUP BY EQP_ID
ORDER BY EQP_ID;
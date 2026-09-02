-- 动力层模板: get_equipment_yield —— 平均良率（指定设备一行；NULL 时按设备排名）
-- 参数: (start_time, end_time, eqp_id | NULL = 全部设备)
SELECT EQP_ID                           AS "设备编号",
       ROUND(AVG(YIELD_RATE) * 100, 2)  AS "平均良率(%)",
       COUNT(*)                         AS "统计晶圆数",
       MIN(MEASURE_TIME)                AS "最早量测时间",
       MAX(MEASURE_TIME)                AS "最晚量测时间"
FROM WAFER_METROLOGY
WHERE MEASURE_TIME BETWEEN ? AND ?
  AND EQP_ID = COALESCE(?, EQP_ID)
GROUP BY EQP_ID
ORDER BY "平均良率(%)" DESC;
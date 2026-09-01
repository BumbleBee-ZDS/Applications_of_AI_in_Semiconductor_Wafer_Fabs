-- 动力层模板: get_defect_stats —— 缺陷统计（按设备）
-- 参数: (start_time, end_time, eqp_id | NULL = 全部设备)
SELECT EQP_ID                 AS "设备编号",
       COUNT(*)               AS "量测点数",
       ROUND(AVG(DEFECT_COUNT), 1) AS "平均缺陷数",
       MAX(DEFECT_COUNT)      AS "最大缺陷数"
FROM WAFER_METROLOGY
WHERE MEASURE_TIME BETWEEN ? AND ?
  AND EQP_ID = COALESCE(?, EQP_ID)
GROUP BY EQP_ID
ORDER BY "平均缺陷数" DESC;
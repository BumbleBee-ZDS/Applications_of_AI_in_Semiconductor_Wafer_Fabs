-- 动力层模板: get_defect_high —— 缺陷偏高晶圆清单（缺陷数 > 50）
-- 参数: (start_time, end_time, eqp_id | NULL = 全部设备)
SELECT METROLOGY_ID          AS "量测ID",
       LOT_ID                AS "批次号",
       WAFER_ID              AS "晶圆号",
       EQP_ID                AS "设备编号",
       MEASURE_TIME          AS "量测时间",
       DEFECT_COUNT          AS "缺陷数",
       FILM_THICKNESS        AS "膜厚",
       ROUND(YIELD_RATE * 100, 2) AS "良率(%)"
FROM WAFER_METROLOGY
WHERE DEFECT_COUNT > 50
  AND MEASURE_TIME BETWEEN ? AND ?
  AND EQP_ID = COALESCE(?, EQP_ID)
ORDER BY DEFECT_COUNT DESC
LIMIT 100;
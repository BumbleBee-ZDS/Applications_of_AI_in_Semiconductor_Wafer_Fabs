-- 动力层模板: get_film_abnormal —— 膜厚异常晶圆清单（规格窗口 [4500,5000]A 之外）
-- 参数: (start_time, end_time, eqp_id | NULL = 全部设备)
SELECT METROLOGY_ID          AS "量测ID",
       LOT_ID                AS "批次号",
       WAFER_ID              AS "晶圆号",
       EQP_ID                AS "设备编号",
       MEASURE_TIME          AS "量测时间",
       FILM_THICKNESS        AS "膜厚",
       DEFECT_COUNT          AS "缺陷数",
       ROUND(YIELD_RATE * 100, 2) AS "良率(%)"
FROM WAFER_METROLOGY
WHERE (FILM_THICKNESS > 5000 OR FILM_THICKNESS < 4500)
  AND MEASURE_TIME BETWEEN ? AND ?
  AND EQP_ID = COALESCE(?, EQP_ID)
ORDER BY MEASURE_TIME DESC
LIMIT 100;
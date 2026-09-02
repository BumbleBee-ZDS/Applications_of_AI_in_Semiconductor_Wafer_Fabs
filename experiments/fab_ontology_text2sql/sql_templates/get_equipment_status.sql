-- 动力层模板: get_equipment_status —— 设备状态清单
-- 参数: (eqp_id | NULL = 全部设备)
SELECT EQP_ID           AS "设备编号",
       EQUIPMENT_NAME   AS "设备名称",
       EQUIPMENT_TYPE   AS "设备类型",
       AREA             AS "所在区域",
       STATUS           AS "状态",
       INSTALL_DATE     AS "安装日期"
FROM EQUIPMENT
WHERE EQP_ID = COALESCE(?, EQP_ID)
ORDER BY EQP_ID;
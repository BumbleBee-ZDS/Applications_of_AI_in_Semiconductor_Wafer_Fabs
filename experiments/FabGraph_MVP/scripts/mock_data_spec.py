"""模拟数据规格常量。

从 init_mock_data.py 拆分而来，以满足单文件不超过 300 行的规范。
集中存放：表/字段核心定义、命名风格池、存储过程、历史 SQL 模板。

对应ResNet输入特征配置：核心字段为高置信标注样本，
噪声字段模拟真实历史包袱（无注释、命名混乱）。
"""
from __future__ import annotations

from typing import Any

# 语义类型简写 -> ColumnSemanticType 值
SEM_MAP: dict[str, str] = {
    "pk": "primary_key", "fk": "foreign_key", "measure": "measure",
    "dim": "dimension", "ts": "timestamp", "status": "status_flag",
    "id": "identifier", "param": "parameter", "unk": "unknown",
}

# 混合命名风格池（模拟历史包袱）
UNDER = ["lot_id", "wafer_id", "step_name", "layer_no", "chamber_id",
         "operator_id", "bay_cd", "shift_cd", "route_id", "track_id",
         "recipe_no", "process_step", "hold_reason", "rework_cnt"]
CAMEL = ["recipeId", "stepCount", "yieldRate", "defectCount", "tempVal",
         "pressureVal", "flowRate", "speedVal", "rpmVal", "voltVal",
         "currVal", "powerVal", "offsetVal", "biasVal"]
ABBR = ["WFR_ID", "EQP_ID", "OP_ID", "CHAM_NO", "BAY_CD", "SHP_CD",
        "ROUTE_NO", "TRK_ID", "DEV_CD", "GRP_CD", "LVL_CD", "SRC_CD"]
CODE = [f"C{i:03d}_VAL" for i in range(1, 31)] + [f"P{i:03d}_VAL" for i in range(1, 16)]
DTYPES = ["VARCHAR2(20)", "VARCHAR2(50)", "NUMBER", "DATE", "FLOAT", "NUMBER(10,2)"]

# 表定义：core 字段含语义标签（高置信），extra 字段由噪声生成器补充
# (字段名, 数据类型, 语义简写, 中文语义标签, 置信度)
TABLES_SPEC: dict[str, dict[str, Any]] = {
    "LOT_HISTORY": {
        "desc": "批次历史主表，记录每个lot完整生命周期", "tags": ["lot", "production"],
        "core": [
            ("LOT_ID", "VARCHAR2(20)", "pk", "批次号", 1.0),
            ("WFR_ID", "VARCHAR2(20)", "fk", "晶圆ID", 0.9),
            ("PRODUCT_ID", "VARCHAR2(20)", "dim", "产品编号", 0.85),
            ("STAGE_CD", "VARCHAR2(10)", "status", "工艺阶段代码", 0.7),
            ("LOT_TYPE", "VARCHAR2(5)", "dim", "批次类型", 0.75),
            ("START_DT", "DATE", "ts", "开始日期", 0.9),
            ("END_DT", "DATE", "ts", "结束日期", 0.85),
            ("QTY_IN", "NUMBER", "measure", "投入数量", 0.8),
            ("QTY_OUT", "NUMBER", "measure", "产出数量", 0.8),
            ("STATUS", "VARCHAR2(10)", "status", "状态", 0.9),
            ("HOLD_FLAG", "VARCHAR2(1)", "status", "持货标志", 0.7),
            ("PRIORITY_CD", "VARCHAR2(5)", "dim", "优先级", 0.65),
        ],
    },
    "WAFER_RESULT": {
        "desc": "晶圆测试结果表，按晶圆记录良率与测试数据", "tags": ["wafer", "yield"],
        "core": [
            ("WFR_ID", "VARCHAR2(20)", "pk", "晶圆ID", 1.0),
            ("LOT_ID", "VARCHAR2(20)", "fk", "批次号", 0.9),
            ("EQP_ID", "VARCHAR2(20)", "fk", "设备ID", 0.85),
            ("STEP_CD", "VARCHAR2(10)", "dim", "工步代码", 0.7),
            ("TEST_DT", "DATE", "ts", "测试日期", 0.9),
            ("YIELD_VAL", "FLOAT", "measure", "良率值", 0.85),
            ("PASS_CNT", "NUMBER", "measure", "通过数", 0.8),
            ("FAIL_CNT", "NUMBER", "measure", "失败数", 0.8),
            ("RETEST_FLAG", "VARCHAR2(1)", "status", "复测标志", 0.6),
        ],
    },
    "EQUIPMENT_LOG": {
        "desc": "设备日志表，记录设备状态与利用率", "tags": ["equipment"],
        "core": [
            ("EQP_ID", "VARCHAR2(20)", "pk", "设备ID", 1.0),
            ("EQP_TYPE", "VARCHAR2(15)", "dim", "设备类型", 0.75),
            ("RECIPE_ID", "VARCHAR2(20)", "fk", "配方ID", 0.85),
            ("CHAMBER_NO", "VARCHAR2(10)", "dim", "腔体号", 0.7),
            ("LOG_DT", "DATE", "ts", "日志时间", 0.9),
            ("STATUS_CD", "VARCHAR2(10)", "status", "状态码", 0.8),
            ("PM_DT", "DATE", "ts", "保养日期", 0.8),
            ("UTIL_RATE", "FLOAT", "measure", "利用率", 0.75),
        ],
    },
    "SPC_DATA": {
        "desc": "SPC统计过程控制数据表", "tags": ["spc", "quality"],
        "core": [
            ("SPC_ID", "VARCHAR2(20)", "pk", "SPC记录ID", 1.0),
            ("LOT_ID", "VARCHAR2(20)", "fk", "批次号", 0.9),
            ("EQP_ID", "VARCHAR2(20)", "fk", "设备ID", 0.85),
            ("PARAM_ID", "VARCHAR2(20)", "fk", "参数ID", 0.85),
            ("MEASURE_VAL", "FLOAT", "measure", "测量值", 0.85),
            ("USL", "FLOAT", "measure", "规格上限", 0.75),
            ("LSL", "FLOAT", "measure", "规格下限", 0.75),
            ("MEAS_DT", "DATE", "ts", "测量时间", 0.9),
            ("CHART_TYPE", "VARCHAR2(10)", "dim", "控制图类型", 0.6),
            ("OOC_FLAG", "VARCHAR2(1)", "status", "越界标志", 0.7),
        ],
    },
    "RECIPE_PARAM": {
        "desc": "配方参数表，定义工艺参数目标值", "tags": ["recipe", "param"],
        "core": [
            ("RECIPE_ID", "VARCHAR2(20)", "pk", "配方ID", 1.0),
            ("PARAM_ID", "VARCHAR2(20)", "pk", "参数ID", 1.0),
            ("PARAM_NAME", "VARCHAR2(50)", "dim", "参数名", 0.8),
            ("TARGET_VAL", "FLOAT", "measure", "目标值", 0.8),
            ("TOLERANCE", "FLOAT", "measure", "公差", 0.75),
            ("UNIT", "VARCHAR2(10)", "dim", "单位", 0.7),
            ("STEP_NO", "NUMBER", "dim", "工步号", 0.7),
            ("LAST_UPD_DT", "DATE", "ts", "最后更新时间", 0.85),
        ],
    },
    "YIELD_SUMMARY": {
        "desc": "良率汇总表，按批次汇总产出与良率", "tags": ["yield"],
        "core": [
            ("LOT_ID", "VARCHAR2(20)", "pk", "批次号", 0.95),
            ("PRODUCT_ID", "VARCHAR2(20)", "dim", "产品编号", 0.8),
            ("TOTAL_IN", "NUMBER", "measure", "总投入", 0.8),
            ("TOTAL_OUT", "NUMBER", "measure", "总产出", 0.8),
            ("YIELD_PCT", "FLOAT", "measure", "良率百分比", 0.9),
            ("CALC_DT", "DATE", "ts", "计算日期", 0.85),
            ("GRADE_CD", "VARCHAR2(5)", "dim", "等级代码", 0.65),
        ],
    },
    "DEFECT_DATA": {
        "desc": "缺陷数据表，记录晶圆缺陷明细", "tags": ["defect", "quality"],
        "core": [
            ("DEFECT_ID", "VARCHAR2(20)", "pk", "缺陷ID", 1.0),
            ("WFR_ID", "VARCHAR2(20)", "fk", "晶圆ID", 0.9),
            ("LOT_ID", "VARCHAR2(20)", "fk", "批次号", 0.85),
            ("DEFECT_CD", "VARCHAR2(15)", "dim", "缺陷代码", 0.75),
            ("DEFECT_CNT", "NUMBER", "measure", "缺陷数量", 0.85),
            ("SIZE_VAL", "FLOAT", "measure", "缺陷尺寸", 0.7),
            ("COORD_X", "FLOAT", "measure", "X坐标", 0.65),
            ("COORD_Y", "FLOAT", "measure", "Y坐标", 0.65),
            ("INSPECT_DT", "DATE", "ts", "检测时间", 0.85),
            ("INSPECTOR_ID", "VARCHAR2(20)", "id", "检测员ID", 0.7),
        ],
    },
    "PROCESS_FLOW": {
        "desc": "工艺流程表，记录批次在各工步的流转", "tags": ["flow", "production"],
        "core": [
            ("FLOW_ID", "VARCHAR2(20)", "pk", "流程ID", 1.0),
            ("LOT_ID", "VARCHAR2(20)", "fk", "批次号", 0.9),
            ("STAGE_CD", "VARCHAR2(10)", "dim", "阶段代码", 0.7),
            ("STEP_SEQ", "NUMBER", "dim", "工步顺序", 0.75),
            ("STEP_NAME", "VARCHAR2(50)", "dim", "工步名", 0.75),
            ("EQP_ID", "VARCHAR2(20)", "fk", "设备ID", 0.85),
            ("START_DT", "DATE", "ts", "开始时间", 0.9),
            ("END_DT", "DATE", "ts", "结束时间", 0.85),
            ("DURATION_VAL", "FLOAT", "measure", "持续时长", 0.75),
        ],
    },
}

# 存储过程：每个过程作为血缘超边连接读取/写入的表
PROCEDURES_SPEC: list[dict[str, Any]] = [
    {"name": "SP_CALC_YIELD", "desc": "按批次计算良率并写入汇总表",
     "inputs": ["LOT_HISTORY", "WAFER_RESULT"], "outputs": ["YIELD_SUMMARY"]},
    {"name": "SP_AGGREGATE_DEFECT", "desc": "聚合缺陷数据回写良率汇总",
     "inputs": ["DEFECT_DATA", "WAFER_RESULT"], "outputs": ["YIELD_SUMMARY"]},
    {"name": "SP_PROCESS_TRACE", "desc": "追溯批次工艺流程并更新设备日志",
     "inputs": ["PROCESS_FLOW", "LOT_HISTORY", "EQUIPMENT_LOG"], "outputs": ["EQUIPMENT_LOG"]},
    {"name": "SP_RECIPE_VALIDATION", "desc": "校验配方参数与SPC测量偏差",
     "inputs": ["RECIPE_PARAM", "EQUIPMENT_LOG", "SPC_DATA"], "outputs": []},
    {"name": "SP_WAFER_INSPECT", "desc": "根据测试失败数插入缺陷记录",
     "inputs": ["WAFER_RESULT"], "outputs": ["DEFECT_DATA"]},
    {"name": "SP_DAILY_YIELD_REPORT", "desc": "生成每日良率报告",
     "inputs": ["LOT_HISTORY", "YIELD_SUMMARY", "PROCESS_FLOW"], "outputs": []},
]

# 历史 SQL：(类别, SQL文本) —— 50+ 条，覆盖各类模式
SQL_HISTORY: list[tuple[str, str]] = [
    ("simple", "SELECT * FROM LOT_HISTORY WHERE STATUS = 'ACTIVE'"),
    ("simple", "SELECT LOT_ID, PRODUCT_ID, QTY_IN, QTY_OUT FROM LOT_HISTORY WHERE LOT_TYPE = 'P'"),
    ("simple", "SELECT WFR_ID, YIELD_VAL FROM WAFER_RESULT WHERE TEST_DT >= '2024-01-01'"),
    ("simple", "SELECT EQP_ID, STATUS_CD FROM EQUIPMENT_LOG WHERE UTIL_RATE > 0.8"),
    ("simple", "SELECT DEFECT_ID, DEFECT_CD, DEFECT_CNT FROM DEFECT_DATA WHERE DEFECT_CNT > 10"),
    ("simple", "SELECT RECIPE_ID, PARAM_NAME, TARGET_VAL FROM RECIPE_PARAM"),
    ("simple", "SELECT * FROM SPC_DATA WHERE OOC_FLAG = 'Y'"),
    ("simple", "SELECT LOT_ID, YIELD_PCT FROM YIELD_SUMMARY WHERE YIELD_PCT < 0.9"),
    ("join", "SELECT l.LOT_ID, l.PRODUCT_ID, w.YIELD_VAL FROM LOT_HISTORY l JOIN WAFER_RESULT w ON l.WFR_ID = w.WFR_ID"),
    ("join", "SELECT w.WFR_ID, d.DEFECT_CNT FROM WAFER_RESULT w JOIN DEFECT_DATA d ON w.WFR_ID = d.WFR_ID"),
    ("join", "SELECT l.LOT_ID, y.YIELD_PCT FROM LOT_HISTORY l JOIN YIELD_SUMMARY y ON l.LOT_ID = y.LOT_ID"),
    ("join", "SELECT e.EQP_ID, s.MEASURE_VAL FROM EQUIPMENT_LOG e JOIN SPC_DATA s ON e.EQP_ID = s.EQP_ID"),
    ("join", "SELECT r.RECIPE_ID, r.PARAM_NAME, s.MEASURE_VAL FROM RECIPE_PARAM r JOIN SPC_DATA s ON r.PARAM_ID = s.PARAM_ID"),
    ("join", "SELECT l.LOT_ID, p.STEP_NAME FROM LOT_HISTORY l JOIN PROCESS_FLOW p ON l.LOT_ID = p.LOT_ID"),
    ("join", "SELECT l.LOT_ID, l.PRODUCT_ID, w.YIELD_VAL, d.DEFECT_CNT FROM LOT_HISTORY l JOIN WAFER_RESULT w ON l.WFR_ID = w.WFR_ID JOIN DEFECT_DATA d ON w.WFR_ID = d.WFR_ID"),
    ("join", "SELECT l.LOT_ID, y.YIELD_PCT, s.MEASURE_VAL FROM LOT_HISTORY l JOIN YIELD_SUMMARY y ON l.LOT_ID=y.LOT_ID JOIN SPC_DATA s ON l.LOT_ID=s.LOT_ID"),
    ("join", "SELECT e.EQP_ID, e.EQP_TYPE, s.PARAM_ID, s.MEASURE_VAL FROM EQUIPMENT_LOG e JOIN SPC_DATA s ON e.EQP_ID=s.EQP_ID JOIN RECIPE_PARAM r ON s.PARAM_ID=r.PARAM_ID"),
    ("join", "SELECT p.STEP_NAME, p.EQP_ID, e.EQP_TYPE FROM PROCESS_FLOW p JOIN EQUIPMENT_LOG e ON p.EQP_ID=e.EQP_ID"),
    ("join", "SELECT w.WFR_ID, w.LOT_ID, l.PRODUCT_ID FROM WAFER_RESULT w JOIN LOT_HISTORY l ON w.LOT_ID=l.LOT_ID"),
    ("join", "SELECT d.WFR_ID, d.DEFECT_CD, w.STEP_CD FROM DEFECT_DATA d JOIN WAFER_RESULT w ON d.WFR_ID=w.WFR_ID"),
    ("join", "SELECT s.LOT_ID, s.MEASURE_VAL, r.TARGET_VAL FROM SPC_DATA s JOIN RECIPE_PARAM r ON s.PARAM_ID=r.PARAM_ID JOIN LOT_HISTORY l ON s.LOT_ID=l.LOT_ID"),
    ("join", "SELECT y.LOT_ID, y.YIELD_PCT, l.STATUS FROM YIELD_SUMMARY y JOIN LOT_HISTORY l ON y.LOT_ID=l.LOT_ID"),
    ("join", "SELECT p.LOT_ID, p.STEP_NAME, p.DURATION_VAL, e.EQP_TYPE FROM PROCESS_FLOW p JOIN EQUIPMENT_LOG e ON p.EQP_ID=e.EQP_ID JOIN LOT_HISTORY l ON p.LOT_ID=l.LOT_ID"),
    ("aggregate", "SELECT l.PRODUCT_ID, COUNT(*) AS lot_cnt FROM LOT_HISTORY l GROUP BY l.PRODUCT_ID"),
    ("aggregate", "SELECT l.LOT_ID, AVG(w.YIELD_VAL) AS avg_yield FROM LOT_HISTORY l JOIN WAFER_RESULT w ON l.WFR_ID=w.WFR_ID GROUP BY l.LOT_ID"),
    ("aggregate", "SELECT e.EQP_ID, MAX(s.MEASURE_VAL) AS max_val, MIN(s.MEASURE_VAL) AS min_val FROM EQUIPMENT_LOG e JOIN SPC_DATA s ON e.EQP_ID=s.EQP_ID GROUP BY e.EQP_ID"),
    ("aggregate", "SELECT l.PRODUCT_ID, SUM(l.QTY_IN) AS tot_in, SUM(l.QTY_OUT) AS tot_out FROM LOT_HISTORY l GROUP BY l.PRODUCT_ID"),
    ("aggregate", "SELECT d.DEFECT_CD, COUNT(*) AS cnt, AVG(d.DEFECT_CNT) AS avg_cnt FROM DEFECT_DATA d GROUP BY d.DEFECT_CD"),
    ("aggregate", "SELECT l.LOT_ID, AVG(w.YIELD_VAL) AS avg_yield, MAX(d.DEFECT_CNT) AS max_defect FROM LOT_HISTORY l JOIN WAFER_RESULT w ON l.WFR_ID=w.WFR_ID JOIN DEFECT_DATA d ON w.WFR_ID=d.WFR_ID GROUP BY l.LOT_ID"),
    ("aggregate", "SELECT TO_CHAR(s.MEAS_DT,'YYYY-MM') AS mon, AVG(s.MEASURE_VAL) AS avg_val FROM SPC_DATA s GROUP BY TO_CHAR(s.MEAS_DT,'YYYY-MM')"),
    ("aggregate", "SELECT r.RECIPE_ID, COUNT(s.SPC_ID) AS spc_cnt FROM RECIPE_PARAM r LEFT JOIN SPC_DATA s ON r.PARAM_ID=s.PARAM_ID GROUP BY r.RECIPE_ID"),
    ("aggregate", "SELECT p.STEP_NAME, AVG(p.DURATION_VAL) AS avg_dur FROM PROCESS_FLOW p GROUP BY p.STEP_NAME"),
    ("aggregate", "SELECT l.LOT_TYPE, COUNT(*) AS cnt FROM LOT_HISTORY l WHERE l.STATUS='ACTIVE' GROUP BY l.LOT_TYPE"),
    ("subquery", "SELECT LOT_ID, PRODUCT_ID FROM LOT_HISTORY WHERE LOT_ID IN (SELECT LOT_ID FROM YIELD_SUMMARY WHERE YIELD_PCT < 0.85)"),
    ("subquery", "SELECT WFR_ID, YIELD_VAL FROM WAFER_RESULT WHERE YIELD_VAL < (SELECT AVG(YIELD_VAL) FROM WAFER_RESULT)"),
    ("subquery", "SELECT l.LOT_ID FROM LOT_HISTORY l WHERE l.LOT_ID IN (SELECT LOT_ID FROM DEFECT_DATA WHERE DEFECT_CNT > 50)"),
    ("subquery", "SELECT EQP_ID, UTIL_RATE FROM EQUIPMENT_LOG WHERE UTIL_RATE > (SELECT AVG(UTIL_RATE) FROM EQUIPMENT_LOG)"),
    ("subquery", "SELECT PRODUCT_ID, COUNT(*) FROM LOT_HISTORY WHERE PRODUCT_ID IN (SELECT PRODUCT_ID FROM YIELD_SUMMARY WHERE YIELD_PCT > 0.95) GROUP BY PRODUCT_ID"),
    ("subquery", "SELECT LOT_ID, QTY_OUT FROM LOT_HISTORY WHERE QTY_OUT < (SELECT AVG(QTY_OUT) FROM LOT_HISTORY WHERE LOT_TYPE='P')"),
    ("subquery", "SELECT s.LOT_ID, s.MEASURE_VAL FROM SPC_DATA s WHERE s.MEASURE_VAL > (SELECT TARGET_VAL FROM RECIPE_PARAM WHERE PARAM_ID=s.PARAM_ID)"),
    ("subquery", "SELECT d.WFR_ID FROM DEFECT_DATA d WHERE d.DEFECT_CNT > (SELECT AVG(DEFECT_CNT) FROM DEFECT_DATA WHERE DEFECT_CD=d.DEFECT_CD)"),
    ("lineage", "INSERT INTO YIELD_SUMMARY (LOT_ID, PRODUCT_ID, TOTAL_IN, TOTAL_OUT, YIELD_PCT, CALC_DT) SELECT l.LOT_ID, l.PRODUCT_ID, SUM(l.QTY_IN), SUM(l.QTY_OUT), SUM(l.QTY_OUT)/SUM(l.QTY_IN), SYSDATE FROM LOT_HISTORY l WHERE l.STATUS='CLOSED' GROUP BY l.LOT_ID, l.PRODUCT_ID"),
    ("lineage", "INSERT INTO DEFECT_DATA (DEFECT_ID, WFR_ID, LOT_ID, DEFECT_CD, DEFECT_CNT, INSPECT_DT) SELECT SEQ_DEF.NEXTVAL, w.WFR_ID, w.LOT_ID, 'SCRATCH', 0, SYSDATE FROM WAFER_RESULT w WHERE w.FAIL_CNT > 0"),
    ("lineage", "INSERT INTO SPC_DATA (SPC_ID, LOT_ID, EQP_ID, PARAM_ID, MEASURE_VAL, MEAS_DT) SELECT SEQ_SPC.NEXTVAL, s.LOT_ID, s.EQP_ID, s.PARAM_ID, s.MEASURE_VAL, SYSDATE FROM SPC_DATA s WHERE s.MEAS_DT < SYSDATE-30"),
    ("lineage", "INSERT INTO PROCESS_FLOW (FLOW_ID, LOT_ID, STAGE_CD, STEP_SEQ, START_DT) SELECT SEQ_FLOW.NEXTVAL, l.LOT_ID, l.STAGE_CD, 1, l.START_DT FROM LOT_HISTORY l WHERE l.STATUS='ACTIVE'"),
    ("lineage", "INSERT INTO YIELD_SUMMARY(LOT_ID, PRODUCT_ID, TOTAL_OUT, YIELD_PCT) SELECT l.LOT_ID, l.PRODUCT_ID, l.QTY_OUT, l.QTY_OUT/l.QTY_IN FROM LOT_HISTORY l JOIN WAFER_RESULT w ON l.WFR_ID=w.WFR_ID"),
    ("lineage", "INSERT INTO DEFECT_DATA (WFR_ID, LOT_ID, DEFECT_CNT) SELECT d.WFR_ID, d.LOT_ID, SUM(d.DEFECT_CNT) FROM DEFECT_DATA d GROUP BY d.WFR_ID, d.LOT_ID"),
    ("lineage", "INSERT INTO SPC_DATA (LOT_ID, EQP_ID, PARAM_ID, MEASURE_VAL) SELECT s.LOT_ID, s.EQP_ID, r.PARAM_ID, s.MEASURE_VAL FROM SPC_DATA s JOIN RECIPE_PARAM r ON s.PARAM_ID=r.PARAM_ID"),
    ("join", "SELECT l.LOT_ID, l.PRODUCT_ID, y.YIELD_PCT FROM LOT_HISTORY l LEFT JOIN YIELD_SUMMARY y ON l.LOT_ID=y.LOT_ID WHERE y.YIELD_PCT IS NULL"),
    ("subquery", "SELECT * FROM (SELECT LOT_ID, AVG(YIELD_VAL) AS y FROM WAFER_RESULT GROUP BY LOT_ID) WHERE y > 0.95"),
    ("aggregate", "SELECT e.EQP_TYPE, COUNT(s.SPC_ID) AS cnt FROM EQUIPMENT_LOG e LEFT JOIN SPC_DATA s ON e.EQP_ID=s.EQP_ID GROUP BY e.EQP_TYPE"),
    ("aggregate", "SELECT LOT_ID, COUNT(*) AS step_cnt FROM PROCESS_FLOW GROUP BY LOT_ID HAVING COUNT(*) > 5"),
    ("lineage", "MERGE INTO YIELD_SUMMARY y USING (SELECT LOT_ID, AVG(YIELD_VAL) AS v FROM WAFER_RESULT GROUP BY LOT_ID) w ON (y.LOT_ID=w.LOT_ID) WHEN MATCHED THEN UPDATE SET y.YIELD_PCT=w.v"),
]

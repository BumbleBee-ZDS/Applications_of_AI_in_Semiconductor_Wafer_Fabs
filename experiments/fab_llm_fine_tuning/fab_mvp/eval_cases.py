"""
评估用例集 (覆盖不同意图, 用于 UI 示例与效果评估)
每条: (问题, 期望意图, 期望模板, 说明)
"""
EVAL_CASES = [
    ("昨天3号机良率掉的厉害咋回事", "yield_analysis", "SQL_TMPL_YIELD_01", "口语+机台编号模糊指代"),
    ("FAB8那边PROD-A的CP yield掉得夸张", "yield_analysis", "SQL_TMPL_YIELD_01", "厂区+产品+缩写"),
    ("L28那批货卡在hold好几天了", "hold_query", "SQL_TMPL_HOLD_01", "产品缩写+hold黑话"),
    ("刻蚀那台设备有OOC没处理完的", "spc_alarm", "SQL_TMPL_SPC_01", "设备类型+OOC缩写"),
    ("3号光刻机PM之后有没有异常", "pm_analysis", "SQL_TMPL_PM_01", "PM黑话+机台"),
    ("WAT那边有个lot颗粒缺陷爆表了看热点", "defect_analysis", "SQL_TMPL_DEFECT_01", "WAT+缺陷黑话"),
    ("帮我追溯一下LOT-A2034怎么走的", "lot_trace", "SQL_TMPL_TRACE_01", "追溯+批次号"),
    ("最近刻蚀参数是不是漂了", "process_param", "SQL_TMPL_PROCESS_01", "参数漂移口语"),
    ("CMP那台设备down了影响哪些批次", "equipment_abnormal", "SQL_TMPL_EQUIP_01", "down机+影响"),
    ("上周CP良率低于85的批次有哪些", "yield_analysis", "SQL_TMPL_YIELD_01", "良率阈值明确"),
]

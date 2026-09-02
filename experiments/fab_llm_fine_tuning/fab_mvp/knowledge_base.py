"""
模拟晶圆厂(半导体制造)知识库 MVP
============================================================
包含 4 部分:
  1. FAB_SCHEMA   表结构 + 字段解密(真实场景字段无注释, 以下"解密"含义即领域知识)
  2. GLOSSARY     缩写词典(CP/FT/WAT/SPC 等黑话)
  3. SQL_TEMPLATES SQL模板库(晶圆厂多年沉淀的分析SQL)
  4. SOP_SNIPPETS  SOP流程片段(尘封但有价值的领域知识)

用途:
  - 作为 DeepSeek 合成训练数据的知识源
  - 定义小模型微调需掌握的领域知识边界
  - 强模型生成最终SQL/回答时的参考上下文
"""

# ============================================================
# ResNet Step 1: 模拟晶圆厂表结构 + 字段解密
# 说明: 字段名用 Oracle 风格大写下划线; "meaning"是解密含义(真实库无注释)
#       小模型需学习 LOT_ID->批次号 这类映射, 这是核心领域知识
# ============================================================
FAB_SCHEMA = {
    "WIP_LOT": {
        "desc": "在制品批次主表, 记录每个lot流转状态(数据量百万级)",
        "columns": {
            "LOT_ID": "批次号, 唯一标识一批晶圆(25片/批)",
            "WAFER_ID": "晶圆唯一ID",
            "PRODUCT_ID": "产品型号(如 PROD-A28nm)",
            "ROUTE_ID": "工艺路线ID, 定义工序顺序",
            "OPER_ID": "当前工序号(如 OPO3050 光刻)",
            "OPER_NAME": "工序名称缩写",
            "EQP_ID": "当前所在设备ID",
            "CHAMBER_ID": "腔室号(多腔室设备)",
            "LOT_STATUS": "批次状态: WAIT/RUN/HOLD/DONE/SCRAP",
            "START_TIME": "进入当前工序时间",
            "END_TIME": "完成当前工序时间",
            "QTY_IN": "投入数量(片)",
            "QTY_OUT": "产出数量(片)",
            "HOLD_CODE": "hold原因代码(如 H001=等机台)",
            "PRIORITY": "优先级(1-9, 1最高)",
            "OWNER_ID": "负责工程师工号",
            "FAB_SITE": "厂区代码(FAB8/FAB12)",
            "CUSTOMER": "客户名称",
            "DUE_DATE": "交货日期",
            "REWORK_FLAG": "是否返工(0/1)",
            "HOLD_TIME": "累计hold时长(分钟)",
        },
    },
    "EQUIPMENT": {
        "desc": "设备主数据表, 含状态与维护信息",
        "columns": {
            "EQP_ID": "设备ID(如 EQP-PHOTO-003)",
            "EQP_NAME": "设备名称",
            "EQP_TYPE": "设备类型: PHOTO/LITHO/ETCH/CVD/PVD/CMP/IMP",
            "MODEL": "设备型号",
            "FAB_SITE": "所在厂区",
            "BAY_ID": "所在bay(区)",
            "STATUS": "设备状态: RUN/IDLE/PM/DOWN/ENG",
            "LAST_PM_TIME": "上次PM(保养)时间",
            "NEXT_PM_TIME": "下次PM到期时间",
            "MTBF": "平均无故障时间(小时)",
            "UTIL_RATE": "利用率(%)",
            "CHAMBER_CNT": "腔室数量",
            "VENDOR": "设备厂商(ASML/AMAT/LAM/TEL)",
            "INSTALL_DATE": "安装日期",
            "DOWNTIME_REASON": "down机原因代码",
        },
    },
    "PROCESS_LOG": {
        "desc": "工艺日志表, 每片晶圆每工序一条(数据量极大, 千万级)",
        "columns": {
            "LOG_ID": "日志流水号",
            "LOT_ID": "批次号(关联WIP_LOT)",
            "WAFER_ID": "晶圆ID",
            "EQP_ID": "加工设备(关联EQUIPMENT)",
            "CHAMBER_ID": "腔室号",
            "OPER_ID": "工序号",
            "RECIPE_ID": "配方ID(关联RECIPE)",
            "PARAM_ID": "工艺参数ID",
            "PARAM_VALUE": "参数实测值",
            "PARAM_USL": "参数规格上限",
            "PARAM_LSL": "参数规格下限",
            "PARAM_TARGET": "参数目标值",
            "LOG_TIME": "记录时间",
            "OPERATOR_ID": "操作员工号",
            "SHIFT": "班次(A/B/C)",
            "PASS_FAIL": "本工序合格标志",
        },
    },
    "YIELD_SUMMARY": {
        "desc": "良率汇总表, 按测试阶段汇总(CP/FT/WAT)",
        "columns": {
            "LOT_ID": "批次号",
            "WAFER_ID": "晶圆ID",
            "TEST_STAGE": "测试阶段: CP/FT/WAT/SORT",
            "YIELD_RATE": "良率(%, <85%视为异常)",
            "BIN1_QTY": "良品数量(bin1=good)",
            "BIN_FAIL_QTY": "不良数量",
            "DEFECT_CNT": "缺陷总数",
            "TEST_DATE": "测试日期",
            "TESTER_ID": "测试机台",
            "PROD_ID": "产品型号",
            "BASELINE_YIELD": "历史基线良率(%)",
            "YIELD_DELTA": "良率偏离基线(百分点)",
        },
    },
    "DEFECT_DATA": {
        "desc": "缺陷坐标数据表, 用于缺陷热点分析(地图)",
        "columns": {
            "DEFECT_ID": "缺陷流水号",
            "WAFER_ID": "晶圆ID",
            "LOT_ID": "批次号",
            "X_COORD": "缺陷X坐标(um)",
            "Y_COORD": "缺陷Y坐标(um)",
            "DEFECT_TYPE": "缺陷类型: PARTICLE/SCRATCH/PATTERN/CRYSTAL",
            "SIZE_UM": "缺陷尺寸(um)",
            "LAYER": "所在工艺层",
            "INSPECT_TIME": "检测时间",
            "INSPECTOR": "检测设备",
            "SEVERITY": "严重度: H/M/L",
        },
    },
    "OOC_ALARM": {
        "desc": "SPC异常告警表(Out of Control), 工艺参数越界告警",
        "columns": {
            "ALARM_ID": "告警流水号",
            "EQP_ID": "告警设备",
            "PARAM_ID": "告警参数",
            "OPER_ID": "工序号",
            "ALARM_TYPE": "告警类型: OOC/OOS/WESTERN_RULE",
            "ALARM_VALUE": "触发值",
            "CONTROL_LIMIT": "控制限",
            "ALARM_TIME": "告警时间",
            "LOT_ID": "关联批次",
            "DISPOSITION": "处置状态: OPEN/CLOSED/HOLD",
            "ACTION_TAKEN": "已采取措施",
            "OWNER": "处理工程师",
        },
    },
    "RECIPE": {
        "desc": "配方表, 定义设备加工参数集",
        "columns": {
            "RECIPE_ID": "配方ID",
            "RECIPE_NAME": "配方名称",
            "EQP_TYPE": "适用设备类型",
            "OPER_ID": "适用工序",
            "VERSION": "版本号",
            "PARAM_SET": "参数集(JSON)",
            "CREATE_TIME": "创建时间",
            "APPROVE_STATUS": "审批状态",
            "CREATOR": "创建人",
        },
    },
}


# ============================================================
# ResNet Step 2: 缩写词典(GLOSSARY)
# 晶圆厂黑话/缩写, 强模型通常不懂, 小模型需学习
# ============================================================
GLOSSARY = {
    "CP": "Circuit Probing, 晶圆测试/探针测试, 出货前对整片晶圆的芯片做电性测试",
    "FT": "Final Test, 成品测试, 切割封装后对单个芯片做最终电性测试",
    "WAT": "Wafer Acceptance Test, 晶圆验收测试, 工艺监控用测试键",
    "SORT": "Wafer Sort, 晶圆级分选, 等同CP",
    "CIM": "Computer Integrated Manufacturing, 计算机集成制造系统",
    "MES": "Manufacturing Execution System, 制造执行系统, 管控lot流转",
    "EAP": "Equipment Automation Program, 设备自动化程序",
    "SPC": "Statistical Process Control, 统计过程控制",
    "OOC": "Out of Control, 失控(参数超出控制限)",
    "OOS": "Out of Specification, 超规格(参数超出规格限)",
    "PM": "Preventive Maintenance, 预防性保养",
    "MRB": "Material Review Board, 物料审查委员会, 处理异常批次",
    "WIP": "Work In Progress, 在制品",
    "FOUP": "Front Opening Unified Pod, 晶圆传送盒(装25片)",
    "POD": "晶圆盒/载具",
    "Reticle": "光罩/掩膜版, 光刻用",
    "Recipe": "配方, 设备加工参数集合",
    "Route": "工艺路线, 工序顺序定义",
    "Operation/Oper": "工序",
    "Lot": "批次, 通常25片晶圆为一批",
    "Wafer": "晶圆, 硅片",
    "Chamber": "腔室, 设备内独立加工单元",
    "EQP": "Equipment, 设备",
    "Bin": "分级, 测试后按良品/不良品分级(bin1=良品)",
    "Yield": "良率",
    "Defect": "缺陷",
    "Hotspot": "缺陷热点, 晶圆上缺陷聚集区域",
    "Rework": "返工",
    "Scrap": "报废",
    "Hold": "批扣留, 暂停流转",
    "DC": "Data Collection, 数据采集",
    "EO": "Engineering Order, 工程变更单",
    "BIB": "Bump In Bond, 凸块",
    "RDL": "Redistribution Layer, 重布线层",
    "MPW": "Multi Project Wafer, 多项目晶圆",
}


# ============================================================
# ResNet Step 3: SQL模板库(SQL_TEMPLATES)
# 晶圆厂多年沉淀的分析SQL模板, 小模型学习"问题->模板"映射
# ============================================================
SQL_TEMPLATES = {
    "SQL_TMPL_YIELD_01": {
        "desc": "良率异常批次查询(找YIELD_RATE<基线的lot)",
        "applies_to": "良率下降/良率异常/低良率批次",
        "tables": ["YIELD_SUMMARY", "WIP_LOT"],
        "sql": "SELECT l.LOT_ID, l.PRODUCT_ID, y.YIELD_RATE, y.YIELD_DELTA, y.DEFECT_CNT "
               "FROM YIELD_SUMMARY y JOIN WIP_LOT l ON l.LOT_ID=y.LOT_ID "
               "WHERE y.TEST_STAGE='CP' AND y.YIELD_RATE < y.BASELINE_YIELD - 5 "
               "AND y.TEST_DATE >= :start_date ORDER BY y.YIELD_DELTA ASC",
    },
    "SQL_TMPL_EQUIP_01": {
        "desc": "设备关联异常批次(某设备加工的lot良率对比)",
        "applies_to": "某机台/设备导致良率/异常",
        "tables": ["PROCESS_LOG", "YIELD_SUMMARY", "EQUIPMENT"],
        "sql": "SELECT p.EQP_ID, e.EQP_NAME, p.LOT_ID, y.YIELD_RATE "
               "FROM PROCESS_LOG p JOIN YIELD_SUMMARY y ON y.LOT_ID=p.LOT_ID "
               "JOIN EQUIPMENT e ON e.EQP_ID=p.EQP_ID "
               "WHERE p.EQP_ID=:eqp_id AND p.LOG_TIME>=:start_date",
    },
    "SQL_TMPL_DEFECT_01": {
        "desc": "缺陷热点分析(按类型/坐标聚合)",
        "applies_to": "缺陷/粒子/刮痕/particle/热点",
        "tables": ["DEFECT_DATA", "YIELD_SUMMARY"],
        "sql": "SELECT DEFECT_TYPE, COUNT(*) CNT, AVG(SIZE_UM) AVG_SIZE "
               "FROM DEFECT_DATA WHERE WAFER_ID=:wafer_id GROUP BY DEFECT_TYPE ORDER BY CNT DESC",
    },
    "SQL_TMPL_TRACE_01": {
        "desc": "批次全流程追溯(查lot经过的所有工序/设备)",
        "applies_to": "追溯/trace/某批怎么走的/历史",
        "tables": ["PROCESS_LOG", "WIP_LOT"],
        "sql": "SELECT OPER_ID, EQP_ID, CHAMBER_ID, LOG_TIME, PASS_FAIL "
               "FROM PROCESS_LOG WHERE LOT_ID=:lot_id ORDER BY LOG_TIME",
    },
    "SQL_TMPL_SPC_01": {
        "desc": "SPC OOC告警查询(未关闭的告警)",
        "applies_to": "OOC/SPC/告警/参数越界/失控",
        "tables": ["OOC_ALARM", "EQUIPMENT"],
        "sql": "SELECT a.ALARM_ID, a.EQP_ID, a.PARAM_ID, a.ALARM_VALUE, a.ALARM_TIME "
               "FROM OOC_ALARM a WHERE a.DISPOSITION='OPEN' AND a.ALARM_TIME>=:start_date",
    },
    "SQL_TMPL_PM_01": {
        "desc": "PM前后良率对比(保养效果评估)",
        "applies_to": "PM/保养后/保养影响/保养前后",
        "tables": ["EQUIPMENT", "PROCESS_LOG", "YIELD_SUMMARY"],
        "sql": "SELECT y.LOT_ID, y.YIELD_RATE, p.LOG_TIME "
               "FROM PROCESS_LOG p JOIN YIELD_SUMMARY y ON y.LOT_ID=p.LOT_ID "
               "WHERE p.EQP_ID=:eqp_id AND p.LOG_TIME BETWEEN :pm_time-2 AND :pm_time+2",
    },
    "SQL_TMPL_PROCESS_01": {
        "desc": "工艺参数偏离分析(参数超出规格)",
        "applies_to": "参数偏/工艺漂移/参数超规/recipe",
        "tables": ["PROCESS_LOG"],
        "sql": "SELECT LOT_ID, WAFER_ID, PARAM_VALUE, PARAM_USL, PARAM_LSL, LOG_TIME "
               "FROM PROCESS_LOG WHERE PARAM_ID=:param_id "
               "AND (PARAM_VALUE>PARAM_USL OR PARAM_VALUE<PARAM_LSL) AND LOG_TIME>=:start_date",
    },
    "SQL_TMPL_HOLD_01": {
        "desc": "Hold批次查询(扣留批次及原因)",
        "applies_to": "hold/扣留/卡住/不动/停滞",
        "tables": ["WIP_LOT"],
        "sql": "SELECT LOT_ID, PRODUCT_ID, OPER_ID, HOLD_CODE, HOLD_TIME, OWNER_ID "
               "FROM WIP_LOT WHERE LOT_STATUS='HOLD' AND HOLD_TIME>:threshold",
    },
}


# ============================================================
# ResNet Step 4: SOP片段(SOP_SNIPPETS)
# 尘封但有价值的领域流程知识
# ============================================================
SOP_SNIPPETS = {
    "SOP_YIELD_DROP": (
        "良率下降处理SOP: 当CP良率低于基线5个百分点, "
        "1)先查YIELD_SUMMARY确认异常lot范围与BIN分布; "
        "2)关联PROCESS_LOG看异常lot是否集中在某台EQP/CHAMBER; "
        "3)查DEFECT_DATA做缺陷热点分析判断缺陷类型; "
        "4)查OOC_ALARM看同期是否有SPC告警; "
        "5)若集中在某设备且该设备近期有PM, 用SQL_TMPL_PM_01做PM前后对比"
    ),
    "SOP_EQUIP_DOWN": (
        "设备down机处理SOP: 设备STATUS=DOWN时, "
        "1)查EQUIPMENT.DOWNTIME_REASON; "
        "2)用SQL_TMPL_EQUIP_01回溯该设备近期加工lot的良率; "
        "3)对在制lot做HOLD(MRB介入); "
        "4)若涉及光罩查Reticle使用记录"
    ),
    "SOP_OOC_HANDLE": (
        "OOC处置SOP: SPC告警触发后, "
        "1)用SQL_TMPL_SPC_01查OPEN告警; "
        "2)关联告警参数对应的LOT_ID; "
        "3)对受影响lot做HOLD等待DISPOSITION; "
        "4)工程判断后CLOSE告警并记录ACTION_TAKEN"
    ),
    "SOP_LOT_TRACE": (
        "批次追溯SOP: 客诉或异常追溯时, "
        "1)用SQL_TMPL_TRACE_01查lot全流程工序/设备; "
        "2)对比同ROUTE其他lot找差异工序; "
        "3)查差异工序的PROCESS_LOG参数是否偏离"
    ),
    "SOP_DEFECT_ANALYSIS": (
        "缺陷分析SOP: 良率损失归因时, "
        "1)用SQL_TMPL_DEFECT_01按DEFECT_TYPE聚合; "
        "2)PARTICLE型多来自环境/设备, SCRATCH型多来自搬运; "
        "3)结合X/Y_COORD做wafer map判断热点位置"
    ),
}


def get_all_knowledge_text() -> str:
    """把知识库拼成纯文本, 供 DeepSeek 合成数据时塞入 prompt"""
    lines = ["# 晶圆厂知识库(供参考)\n"]
    lines.append("## 表结构(字段名=解密含义)")
    for t, info in FAB_SCHEMA.items():
        lines.append(f"\n### {t}: {info['desc']}")
        for col, mean in info["columns"].items():
            lines.append(f"- {col}: {mean}")
    lines.append("\n## 缩写词典")
    for k, v in GLOSSARY.items():
        lines.append(f"- {k}: {v}")
    lines.append("\n## SQL模板库")
    for k, v in SQL_TEMPLATES.items():
        lines.append(f"- {k}: {v['desc']} (适用: {v['applies_to']}, 表: {','.join(v['tables'])})")
    lines.append("\n## SOP片段")
    for k, v in SOP_SNIPPETS.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


if __name__ == "__main__":
    # 自检: 打印知识库规模
    print(get_all_knowledge_text()[:2000])
    print(f"\n... 表数: {len(FAB_SCHEMA)}, 缩写: {len(GLOSSARY)}, "
          f"SQL模板: {len(SQL_TEMPLATES)}, SOP: {len(SOP_SNIPPETS)}")

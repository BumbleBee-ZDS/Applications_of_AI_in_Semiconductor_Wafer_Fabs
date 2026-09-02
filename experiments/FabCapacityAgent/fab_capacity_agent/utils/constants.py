"""
FabCapacityAgent - 全局常量定义模块

封装所有枚举值、固定配置、字符串常量，避免魔法数字/硬编码字符串散落在代码各处。
"""

from typing import Dict, List

# =============================================================================
# 工序常量 (Process Constants)
# =============================================================================

# 8道主工序英文代码(业务主键)
PROCESS_PHOTO: str = "PHOTO"     # 光刻
PROCESS_ETCH: str = "ETCH"       # 刻蚀
PROCESS_DEPO: str = "DEPO"       # 沉积
PROCESS_IMP: str = "IMP"         # 离子注入
PROCESS_DIFF: str = "DIFF"       # 扩散
PROCESS_CMP: str = "CMP"         # 抛光
PROCESS_METRO: str = "METRO"     # 量测
PROCESS_WET: str = "WET"         # 清洗

# 所有工序有序列表(按工艺流默认顺序)
ALL_PROCESSES: List[str] = [
    PROCESS_WET,
    PROCESS_PHOTO,
    PROCESS_ETCH,
    PROCESS_DEPO,
    PROCESS_IMP,
    PROCESS_DIFF,
    PROCESS_CMP,
    PROCESS_METRO,
]

# 工序中文名映射
PROCESS_NAME_CN: Dict[str, str] = {
    PROCESS_PHOTO: "光刻",
    PROCESS_ETCH: "刻蚀",
    PROCESS_DEPO: "沉积",
    PROCESS_IMP: "离子注入",
    PROCESS_DIFF: "扩散",
    PROCESS_CMP: "抛光",
    PROCESS_METRO: "量测",
    PROCESS_WET: "清洗",
}

# 工序对应设备类型
PROCESS_EQUIPMENT_TYPE: Dict[str, str] = {
    PROCESS_PHOTO: "Scanner",
    PROCESS_ETCH: "Etcher",
    PROCESS_DEPO: "Deposition",
    PROCESS_IMP: "Implanter",
    PROCESS_DIFF: "Furnace",
    PROCESS_CMP: "CMP_Tool",
    PROCESS_METRO: "Metrology",
    PROCESS_WET: "Wet_Bench",
}

# =============================================================================
# 设备状态常量 (Equipment Status Constants)
# =============================================================================

EQUIP_STATUS_RUN: str = "RUN"       # 运行中(生产)
EQUIP_STATUS_IDLE: str = "IDLE"     # 空闲(无生产任务)
EQUIP_STATUS_DOWN: str = "DOWN"     # 故障停机(非计划停机)
EQUIP_STATUS_PM: str = "PM"         # 预防性维护(计划停机)
EQUIP_STATUS_SETUP: str = "SETUP"   # 换型/调试(产品切换)

# 所有设备状态
ALL_EQUIP_STATUSES: List[str] = [
    EQUIP_STATUS_RUN,
    EQUIP_STATUS_IDLE,
    EQUIP_STATUS_DOWN,
    EQUIP_STATUS_PM,
    EQUIP_STATUS_SETUP,
]

# 设备状态中文名
EQUIP_STATUS_NAME_CN: Dict[str, str] = {
    EQUIP_STATUS_RUN: "运行中",
    EQUIP_STATUS_IDLE: "空闲",
    EQUIP_STATUS_DOWN: "故障停机",
    EQUIP_STATUS_PM: "预防性维护",
    EQUIP_STATUS_SETUP: "换型调试",
}

# 状态对应颜色(UI/Plotly配色)
EQUIP_STATUS_COLOR: Dict[str, str] = {
    EQUIP_STATUS_RUN: "#00FF94",    # 亮绿
    EQUIP_STATUS_IDLE: "#00D4FF",   # 青色
    EQUIP_STATUS_DOWN: "#FF4D6D",   # 红色
    EQUIP_STATUS_PM: "#FFB800",     # 橙色
    EQUIP_STATUS_SETUP: "#C084FC",  # 紫色
}

# =============================================================================
# 产品常量 (Product Constants)
# =============================================================================

PRODUCT_LOGIC_A: str = "Logic_A"     # 逻辑芯片A
PRODUCT_LOGIC_B: str = "Logic_B"     # 逻辑芯片B
PRODUCT_MEMORY_C: str = "Memory_C"   # 存储芯片C

ALL_PRODUCTS: List[str] = [PRODUCT_LOGIC_A, PRODUCT_LOGIC_B, PRODUCT_MEMORY_C]

PRODUCT_NAME_CN: Dict[str, str] = {
    PRODUCT_LOGIC_A: "逻辑芯片A",
    PRODUCT_LOGIC_B: "逻辑芯片B",
    PRODUCT_MEMORY_C: "存储芯片C",
}

# =============================================================================
# KPI指标常量 (KPI Indicator Constants)
# =============================================================================

# OEE三要素
KPI_AVAILABILITY: str = "availability"   # 可用率
KPI_PERFORMANCE: str = "performance"     # 性能率
KPI_QUALITY: str = "quality"             # 良率
KPI_OEE: str = "oee"                     # 综合设备效率 OEE = A × P × Q

# 产出指标
KPI_UPH: str = "uph"                     # 每小时产出 Units Per Hour
KPI_THROUGHPUT: str = "throughput"       # 吞吐量(周期产出)
KPI_MOVE: str = "move"                   # Move数(工序移动步数)
KPI_DAILY_OUTPUT: str = "daily_output"   # 日产出(晶圆数)

# 时间/库存指标
KPI_CYCLE_TIME: str = "cycle_time"       # 周期时间(从入厂到出厂)
KPI_WIP: str = "wip"                     # 在制品数量 Work In Progress
KPI_WAIT_TIME: str = "wait_time"         # 等待时间
KPI_TACT_TIME: str = "tact_time"         # 节拍时间

# 瓶颈指标
KPI_UTILIZATION: str = "utilization"     # 设备利用率
KPI_BOTTLENECK_RATE: str = "bottleneck_rate"  # 瓶颈率

# KPI中文名映射
KPI_NAME_CN: Dict[str, str] = {
    KPI_AVAILABILITY: "可用率",
    KPI_PERFORMANCE: "性能率",
    KPI_QUALITY: "良率",
    KPI_OEE: "综合设备效率(OEE)",
    KPI_UPH: "每小时产出(UPH)",
    KPI_THROUGHPUT: "吞吐量",
    KPI_MOVE: "Move数",
    KPI_DAILY_OUTPUT: "日产出(片)",
    KPI_CYCLE_TIME: "周期时间(h)",
    KPI_WIP: "在制品(WIP)",
    KPI_WAIT_TIME: "等待时间(h)",
    KPI_TACT_TIME: "节拍时间(h)",
    KPI_UTILIZATION: "设备利用率",
    KPI_BOTTLENECK_RATE: "瓶颈率",
}

# KPI单位
KPI_UNIT: Dict[str, str] = {
    KPI_AVAILABILITY: "%",
    KPI_PERFORMANCE: "%",
    KPI_QUALITY: "%",
    KPI_OEE: "%",
    KPI_UPH: "片/h",
    KPI_THROUGHPUT: "片",
    KPI_MOVE: "步",
    KPI_DAILY_OUTPUT: "片",
    KPI_CYCLE_TIME: "h",
    KPI_WIP: "片",
    KPI_WAIT_TIME: "h",
    KPI_TACT_TIME: "h",
    KPI_UTILIZATION: "%",
    KPI_BOTTLENECK_RATE: "%",
}

# =============================================================================
# Agent常量 (Agent Framework Constants)
# =============================================================================

# Agent类型标识
AGENT_PERCEPTION: str = "perception"    # 感知Agent
AGENT_ANALYSIS: str = "analysis"        # 分析Agent
AGENT_DECISION: str = "decision"        # 决策Agent
AGENT_EXECUTION: str = "execution"      # 执行Agent
AGENT_ORCHESTRATOR: str = "orchestrator"  # 编排器

# Agent中文名
AGENT_NAME_CN: Dict[str, str] = {
    AGENT_PERCEPTION: "感知Agent",
    AGENT_ANALYSIS: "分析Agent",
    AGENT_DECISION: "决策Agent",
    AGENT_EXECUTION: "执行Agent",
    AGENT_ORCHESTRATOR: "编排器",
}

# PTA循环阶段
STAGE_PERCEIVE: str = "perceive"        # 感知阶段
STAGE_THINK: str = "think"              # 思考阶段
STAGE_ACT: str = "act"                  # 行动阶段

# 执行状态
STATUS_SUCCESS: str = "success"
STATUS_FAILED: str = "failed"
STATUS_RUNNING: str = "running"
STATUS_PENDING: str = "pending"
STATUS_TIMEOUT: str = "timeout"

# =============================================================================
# 时间常量 (Time Constants)
# =============================================================================

HOURS_PER_DAY: int = 24
DAYS_PER_WEEK: int = 7
HOURS_PER_WEEK: int = HOURS_PER_DAY * DAYS_PER_WEEK       # 168
MINUTES_PER_HOUR: int = 60
SECONDS_PER_MINUTE: int = 60

# =============================================================================
# 数据库表名常量 (Database Table Constants)
# =============================================================================

TABLE_EQUIPMENT: str = "equipment"              # 设备主数据表
TABLE_LOTS: str = "lots"                        # 批次信息表
TABLE_LOT_HISTORY: str = "lot_history"          # 工序历史表
TABLE_EQUIPMENT_EVENTS: str = "equipment_events"  # 设备事件表
TABLE_DAILY_OUTPUT: str = "daily_output"        # 日产出汇总表
TABLE_AGENT_LOGS: str = "agent_logs"            # Agent执行日志表

# =============================================================================
# 事件类型常量 (Event Type Constants)
# =============================================================================

EVENT_LOT_START: str = "LOT_START"              # 批次开工
EVENT_LOT_COMPLETE: str = "LOT_COMPLETE"        # 批次完工
EVENT_EQUIP_DOWN: str = "EQUIP_DOWN"            # 设备故障
EVENT_EQUIP_RECOVER: str = "EQUIP_RECOVER"      # 设备恢复
EVENT_PM_START: str = "PM_START"                # PM开始
EVENT_PM_END: str = "PM_END"                    # PM结束
EVENT_SETUP_START: str = "SETUP_START"          # 换型开始
EVENT_SETUP_END: str = "SETUP_END"              # 换型结束

ALL_EVENT_TYPES: List[str] = [
    EVENT_LOT_START,
    EVENT_LOT_COMPLETE,
    EVENT_EQUIP_DOWN,
    EVENT_EQUIP_RECOVER,
    EVENT_PM_START,
    EVENT_PM_END,
    EVENT_SETUP_START,
    EVENT_SETUP_END,
]

# =============================================================================
# 文件路径常量 (File Path Constants) - 相对fab_capacity_agent根目录
# =============================================================================

DIR_CONFIG: str = "config"
DIR_DATA: str = "data"
DIR_MODELS: str = "models"
DIR_AGENTS: str = "agents"
DIR_SERVICES: str = "services"
DIR_PAGES: str = "pages"
DIR_UTILS: str = "utils"
DIR_TESTS: str = "tests"

FILE_SETTINGS: str = "config/settings.yaml"
FILE_DB_DEFAULT: str = "data/fab_capacity.db"
FILE_REPORT_DIR: str = "data/reports"

# =============================================================================
# UI显示常量 (UI Display Constants)
# =============================================================================

# UI主题色 — 亮色主题 (浅底深字, 偏白)
UI_PRIMARY: str = "#2E5A8F"       # 中蓝主色
UI_BACKGROUND: str = "#F5F7FA"    # 浅灰白背景
UI_ACCENT: str = "#0099CC"        # 深青强调色 (白底可读)
UI_SUCCESS: str = "#00A66E"       # 翠绿
UI_WARNING: str = "#E8A300"       # 金黄
UI_DANGER: str = "#E53935"        # 红色
UI_TEXT: str = "#1A2332"          # 深色文字

# Plotly图表默认配色(循环)
CHART_PALETTE: List[str] = [
    "#00D4FF",  # 青色
    "#FF6B9D",  # 粉红
    "#C084FC",  # 紫色
    "#34D399",  # 翠绿
    "#FBBF24",  # 金黄
    "#F87171",  # 珊瑚红
    "#60A5FA",  # 天蓝
    "#A78BFA",  # 淡紫
]

# 格式化模板
FORMAT_PCT: str = "{:.2%}"          # 百分比显示
FORMAT_NUM_2: str = "{:.2f}"        # 两位小数
FORMAT_NUM_INT: str = "{:,.0f}"     # 千分位整数
FORMAT_DATETIME: str = "%Y-%m-%d %H:%M:%S"
FORMAT_DATE: str = "%Y-%m-%d"
FORMAT_TIME: str = "%H:%M:%S"

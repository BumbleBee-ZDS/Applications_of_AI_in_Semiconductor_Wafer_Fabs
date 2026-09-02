# -*- coding: utf-8 -*-
"""
mock_db.py —— 动态层（Dynamic Layer）：模拟晶圆厂 SQLite 数据库的初始化与 Mock 数据
=========================================================================================

Palantir Ontology 三层架构映射
-------------------------------
┌─────────────────────────────────────────────────────────────┐
│  动态层（Dynamic Layer）：数据本身在「哪里、长什么样」          │
│  本文件负责生成一张真实的 SQLite 数据库（data/fab.db），        │
│  包含 4 张晶圆厂核心业务表：                                  │
│      EQUIPMENT        设备主数据                              │
│      LOT_INFO         批次信息                                │
│      WAFER_METROLOGY  晶圆量测数据（膜厚 / 缺陷数 / 良率）      │
│      PROCESS_LOG      工艺日志                                │
│  （语义层见 ontology_dict.json，动力层见 ontology.py）         │
└─────────────────────────────────────────────────────────────┘

设计要点
--------
1. 所有时间均相对「今天」生成，保证「上周 / 昨天 / 最近N天」等时间
   槽位查询永远有数据可查。
2. 使用固定随机种子（seed=42），同一份数据可复现。
3. 数据里刻意埋入「业务上有意义」的分布：
   - 约 4% 晶圆膜厚超出规格窗口 [4500, 5000] Å（对应「膜厚异常」条件查询）；
   - 少量晶圆缺陷数 > 50（对应「缺陷偏高」条件查询）；
   - 良率与缺陷数 / 膜厚偏差负相关，贴近真实物理。
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "fab.db")

# ---------------------------------------------------------------------------
# Mock 数据源（静态定义，可随意扩展）
# ---------------------------------------------------------------------------
# 设备: (设备编号, 设备名称, 设备类型, 所在区域)
EQUIPMENT_DEFS = [
    ("EQP-001", "光刻机 ASML NXT1930", "PHOTO_LITHO", "黄光区"),
    ("EQP-002", "光刻机 ASML NXT1980", "PHOTO_LITHO", "黄光区"),
    ("EQP-003", "薄膜沉积 CVD 2000",   "DEPOSITION", "薄膜区"),
    ("EQP-004", "刻蚀机 LAM 2300",     "ETCH",       "刻蚀区"),
    ("EQP-005", "刻蚀机 TEL 刻蚀台",   "ETCH",       "刻蚀区"),
    ("EQP-006", "离子注入机 Axcelis",  "IMPLANT",    "注入区"),
    ("EQP-007", "CMP 抛光机 Applied",  "CMP",        "抛光区"),
    ("EQP-008", "量测机 KLA 2800",     "METROLOGY",  "检测区"),
    ("EQP-009", "CD-SEM 线宽量测机",   "METROLOGY",  "检测区"),
    ("EQP-010", "清洗机 SC-500",       "CLEAN",      "清洗区"),
]
# 生产线上主要承担工艺的设备（量测机 EQP-008/009 不承担批量工艺）
PROCESS_EQPS = ["EQP-001", "EQP-002", "EQP-003", "EQP-004",
                "EQP-005", "EQP-006", "EQP-007", "EQP-010"]

PRODUCTS  = ["P-NAND-256Gb", "P-DRAM-16Gb", "P-LOGIC-7nm", "P-MCU-32bit", "P-CMOS-Image"]
CUSTOMERS = ["海思半导体", "紫光展锐", "汇顶科技", "中兴微电子", "比亚迪半导体"]
STAGES    = ["光刻", "刻蚀", "薄膜沉积", "离子注入", "清洗", "CMP", "量测", "出货检验"]

# 工序: (工序名, 配方号, 工艺参数描述)
STEP_DEFS = [
    ("光刻",     "RC-PHOTO-101", "ENERGY=28mJ|FOCUS=-0.05um"),
    ("刻蚀",     "RC-ETCH-205",  "RF_POWER=1200W|PRESSURE=5.2Torr"),
    ("薄膜沉积", "RC-CVD-310",   "TEMP=400C|TGT=5000A"),
    ("离子注入", "RC-IMPL-402",  "DOSE=1.2e13|ENERGY=80KeV"),
    ("清洗",     "RC-CLEAN-501", "TIME=15min|CHEM=SC1"),
    ("CMP",      "RC-CMP-603",   "PRESSURE=3.5psi|SPEED=60rpm"),
    ("量测",     "RC-MET-701",   "POINTS=49|MAP=Full"),
]

# 膜厚规格窗口（Å）与缺陷阈值 —— 与 ontology_dict.json 中的本体条件保持一致
FILM_SPEC = (4500.0, 5000.0)
DEFECT_HIGH_THRESHOLD = 50

_FMT = "%Y-%m-%d %H:%M:%S"


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（row_factory=Row 便于按列名取值）。"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force: bool = False) -> dict:
    """初始化数据库（幂等）。

    - 已存在且未 force：直接返回现有摘要（重复调用安全）。
    - force=True：删除旧库后重建，用于 UI 中「重新生成 Mock 数据」。

    返回 {表名: 行数} 摘要。
    """
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(DB_PATH):
        return get_db_summary()

    rng = random.Random(42)          # 固定种子，保证可复现
    now = datetime.now()

    conn = get_connection()
    try:
        _create_tables(conn)
        _seed_equipment(conn, rng)
        lots = _build_lots(rng, now)
        _seed_lots(conn, lots)
        _seed_wafer_metrology(conn, rng, now, lots)
        _seed_process_log(conn, rng, now, lots)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return get_db_summary()


def get_db_summary() -> dict:
    """返回 {表名: 行数}，供 Streamlit 侧边栏展示数据库状态。"""
    if not os.path.exists(DB_PATH):
        return {}
    conn = get_connection()
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return {t["name"]: conn.execute(f"SELECT COUNT(*) FROM {t['name']}").fetchone()[0] for t in tables}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 建表
# ---------------------------------------------------------------------------
def _create_tables(conn: sqlite3.Connection) -> None:
    """动态层表结构：4 张核心表。"""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS EQUIPMENT (
            EQP_ID          TEXT PRIMARY KEY,   -- 设备编号
            EQUIPMENT_NAME  TEXT,               -- 设备名称
            EQUIPMENT_TYPE  TEXT,               -- 设备类型
            AREA            TEXT,               -- 所在区域
            STATUS          TEXT,               -- 运行状态
            INSTALL_DATE    TEXT                -- 安装日期
        );
        CREATE TABLE IF NOT EXISTS LOT_INFO (
            LOT_ID        TEXT PRIMARY KEY,     -- 批次号
            PRODUCT_ID    TEXT,                 -- 产品
            CUSTOMER      TEXT,                 -- 客户
            LOT_QTY       INTEGER,              -- 批次晶圆数
            STATUS        TEXT,                 -- 状态
            CURRENT_STAGE TEXT,                 -- 当前工序
            START_TIME    TEXT,                 -- 开始时间
            FINISH_TIME   TEXT                  -- 完成时间
        );
        CREATE TABLE IF NOT EXISTS WAFER_METROLOGY (
            METROLOGY_ID   INTEGER PRIMARY KEY AUTOINCREMENT, -- 量测ID
            LOT_ID         TEXT,    -- 批次号
            WAFER_ID       TEXT,    -- 晶圆号
            EQP_ID         TEXT,    -- 设备编号（承担该晶圆工艺的设备）
            MEASURE_TIME   TEXT,    -- 量测时间
            FILM_THICKNESS REAL,    -- 膜厚(Å)
            DEFECT_COUNT   INTEGER, -- 缺陷数(个)
            YIELD_RATE     REAL     -- 良率(0~1)
        );
        CREATE TABLE IF NOT EXISTS PROCESS_LOG (
            LOG_ID       INTEGER PRIMARY KEY AUTOINCREMENT, -- 日志ID
            LOT_ID       TEXT,   -- 批次号
            EQP_ID       TEXT,   -- 设备编号
            PROCESS_STEP TEXT,   -- 工序
            RECIPE_ID    TEXT,   -- 配方号
            STATUS       TEXT,   -- 状态(COMPLETED/RUNNING/PENDING)
            START_TIME   TEXT,   -- 开始时间
            END_TIME     TEXT,   -- 结束时间
            PARAMETER    TEXT    -- 工艺参数
        );
        """
    )


# ---------------------------------------------------------------------------
# 造数
# ---------------------------------------------------------------------------
def _seed_equipment(conn: sqlite3.Connection, rng: random.Random) -> None:
    status_pool = ["RUNNING", "RUNNING", "RUNNING", "IDLE", "IDLE", "MAINTENANCE", "ALARM"]
    for (eqp, name, etype, area) in EQUIPMENT_DEFS:
        install = datetime(2021, 1, 1) + timedelta(days=rng.randint(0, 1200))
        conn.execute(
            "INSERT INTO EQUIPMENT VALUES (?,?,?,?,?,?)",
            (eqp, name, etype, area, rng.choice(status_pool), install.strftime("%Y-%m-%d")),
        )


def _build_lots(rng: random.Random, now: datetime) -> list[dict]:
    """批次时间分布：约 35% 落在最近 7 天（保证「上周/最近N天」查询有数据）、
    40% 落在 7~30 天、25% 落在 30~120 天。"""
    lots = []
    for i in range(36):
        lot_id = f"LOT-{now.year}-{i + 1:03d}"
        r = rng.random()
        if r < 0.35:
            start = now - timedelta(days=rng.uniform(0, 7), hours=rng.uniform(0, 23))
        elif r < 0.75:
            start = now - timedelta(days=rng.uniform(7, 30), hours=rng.uniform(0, 23))
        else:
            start = now - timedelta(days=rng.uniform(30, 120), hours=rng.uniform(0, 23))

        finish = start + timedelta(hours=rng.uniform(10, 60))
        if finish < now:
            status, stage = "COMPLETED", "出货检验"
        else:
            status = "RUNNING" if rng.random() < 0.9 else "HOLD"
            stage = rng.choice(STAGES[:-1])

        lots.append({
            "lot_id":   lot_id,
            "product":  rng.choice(PRODUCTS),
            "customer": rng.choice(CUSTOMERS),
            "qty":      rng.randint(8, 25),
            "status":   status,
            "stage":    stage,
            "start":    start,
            "finish":   finish,
            "eqp":      rng.choice(PROCESS_EQPS),   # 该批次全程主要使用的一台设备
        })
    return lots


def _seed_lots(conn: sqlite3.Connection, lots: list[dict]) -> None:
    rows = [
        (l["lot_id"], l["product"], l["customer"], l["qty"], l["status"],
         l["stage"], l["start"].strftime(_FMT), l["finish"].strftime(_FMT))
        for l in lots
    ]
    conn.executemany(
        "INSERT INTO LOT_INFO VALUES (?,?,?,?,?,?,?,?)", rows
    )


def _seed_wafer_metrology(conn: sqlite3.Connection, rng: random.Random,
                          now: datetime, lots: list[dict]) -> None:
    """晶圆量测表：每批 8~20 片晶圆，膜厚 / 缺陷数 / 良率 按业务分布生成。"""
    rows = []
    for lot in lots:
        n = rng.randint(8, 20)
        window = (lot["finish"] - lot["start"]).total_seconds()
        for j in range(n):
            wafer_id = f'{lot["lot_id"]}-W{j + 1:02d}'
            # 量测时间取批次加工窗口内的一点
            measure_time = lot["start"] + timedelta(seconds=window * rng.uniform(0.05, 0.95))

            # ~4% 晶圆膜厚异常（超出规格窗口）
            abnormal = rng.random() < 0.04
            if abnormal:
                if rng.random() < 0.5:
                    thickness = rng.uniform(FILM_SPEC[1] + 1, FILM_SPEC[1] + 450)      # 偏厚
                else:
                    thickness = rng.uniform(FILM_SPEC[0] - 450, FILM_SPEC[0] - 1)      # 偏薄
            else:
                thickness = rng.gauss(4750, 180)

            defect = max(1, int(rng.gauss(25, 10)))
            if abnormal:
                defect += rng.randint(5, 25)      # 异常点缺陷数偏高，贴近物理

            # 良率与缺陷数 | 膜厚偏差 负相关 + 随机噪声
            yield_rate = (0.97
                          - 0.0035 * max(0, defect - 25)
                          - 0.00002 * abs(thickness - 4750)
                          + rng.gauss(0, 0.02))
            yield_rate = max(0.45, min(0.995, yield_rate))

            rows.append((lot["lot_id"], wafer_id, lot["eqp"],
                         measure_time.strftime(_FMT),
                         round(thickness, 1), defect, round(yield_rate, 4)))
    conn.executemany(
        "INSERT INTO WAFER_METROLOGY "
        "(LOT_ID, WAFER_ID, EQP_ID, MEASURE_TIME, FILM_THICKNESS, DEFECT_COUNT, YIELD_RATE) "
        "VALUES (?,?,?,?,?,?,?)", rows
    )


def _seed_process_log(conn: sqlite3.Connection, rng: random.Random,
                      now: datetime, lots: list[dict]) -> None:
    """工艺日志：每批 5~7 道工序，时间顺序排列；未到时间点的工序记为 PENDING。"""
    rows = []
    for lot in lots:
        n_steps = rng.randint(5, 7)
        steps = rng.sample(STEP_DEFS, n_steps)
        window = (lot["finish"] - lot["start"]).total_seconds()
        for idx, (step, recipe, param) in enumerate(steps):
            s = lot["start"] + timedelta(seconds=window * idx / n_steps)
            e = lot["start"] + timedelta(seconds=window * (idx + 1) / n_steps)
            if e <= now:
                status = "COMPLETED"
            elif s <= now < e:
                status = "RUNNING"
            else:
                status = "PENDING"
            rows.append((lot["lot_id"], lot["eqp"], step, recipe, status,
                         s.strftime(_FMT), e.strftime(_FMT), param))
    conn.executemany(
        "INSERT INTO PROCESS_LOG "
        "(LOT_ID, EQP_ID, PROCESS_STEP, RECIPE_ID, STATUS, START_TIME, END_TIME, PARAMETER) "
        "VALUES (?,?,?,?,?,?,?,?)", rows
    )


if __name__ == "__main__":
    # 独立运行：python mock_db.py -> 初始化并打印摘要
    import pprint
    pprint.pprint(init_db(force=True))
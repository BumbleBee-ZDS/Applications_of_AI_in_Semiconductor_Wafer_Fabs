"""SQLite 数仓：连接管理、建表、seed 数据、外键元数据。

用 SQLite 模拟 Oracle 数仓，DDL/SQL 均按标准 SQL（ANSI）编写。
内置的"隐性知识"如 LOT_STS 编码、DEFECT_CD 前缀规则在 seed 中真实体现，
并会作为注释/约定写入 L2 文档与 FK 元数据表 meta_fk。
"""
from __future__ import annotations

import hashlib
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

from config import get_db_path


# --------------------------------------------------------------------------
# 连接与初始化
# --------------------------------------------------------------------------
def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """建立 SQLite 连接并开启外键约束。

    SQLite 默认不开启外键校验，这里显式打开以贴近 Oracle 语义。
    """
    conn = sqlite3.connect(str(db_path or get_db_path()))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# 表定义：表名 -> (建表 SQL , 外键列列表, 列注释(表内注释字段), 隐性知识说明)。
# 外键用 (列, 目标表.目标列) 表达，便于 extractor 抽取 FK 关系。
_SCHEMA: dict[str, tuple[str, list[tuple[str, str]], str]] = {
    "WIP_LOT": (
        """CREATE TABLE IF NOT EXISTS WIP_LOT (
            LOT_ID      TEXT PRIMARY KEY,
            PRODUCT_ID  TEXT NOT NULL,
            STAGE_CD    TEXT NOT NULL,
            LOT_STS     TEXT NOT NULL,
            QTY_IN      INTEGER,
            WAFER_CNT   INTEGER,
            CREATE_DT   TEXT,
            LAST_MOD_DT TEXT
        )""",
        [("PRODUCT_ID", "PRD_PRODUCT.PRODUCT_ID")],
        "在制品批次表。LOT_STS 隐性编码：01=Released,03=Running,05=Hold(待MRB评审),07=Terminated,99=测试批次(统计查询必须排除)",
    ),
    "WIP_LOT_HIST": (
        """CREATE TABLE IF NOT EXISTS WIP_LOT_HIST (
            HIST_ID      INTEGER PRIMARY KEY AUTOINCREMENT,
            LOT_ID       TEXT NOT NULL,
            STEP_ID      TEXT NOT NULL,
            EQP_ID       TEXT,
            TRACK_OUT_DT TEXT,
            QTY_OUT      INTEGER,
            DEFECT_CNT   INTEGER
        )""",
        [("LOT_ID", "WIP_LOT.LOT_ID"), ("STEP_ID", "ENG_STEP.STEP_ID"), ("EQP_ID", "EQP_EQUIPMENT.EQP_ID")],
        "批次过站历史。QTY_OUT 为过站产出晶圆数；DEFECT_CNT 为本步缺陷数",
    ),
    "PRD_PRODUCT": (
        """CREATE TABLE IF NOT EXISTS PRD_PRODUCT (
            PRODUCT_ID TEXT PRIMARY KEY,
            PRODUCT_NM TEXT,
            TECH_NODE  TEXT,
            DIE_SIZE   REAL,
            LAYER_CNT  INTEGER
        )""",
        [],
        "产品主档。TECH_NODE 存字符串如'28nm'，数值比较需 CAST('28nm' AS INTEGER)之类处理",
    ),
    "PRD_ROUTE": (
        """CREATE TABLE IF NOT EXISTS PRD_ROUTE (
            ROUTE_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
            PRODUCT_ID TEXT NOT NULL,
            STEP_SEQ   INTEGER,
            STEP_ID    TEXT NOT NULL
        )""",
        [("PRODUCT_ID", "PRD_PRODUCT.PRODUCT_ID"), ("STEP_ID", "ENG_STEP.STEP_ID")],
        "产品工艺路线。STEP_SEQ 为工序顺序号",
    ),
    "ENG_STEP": (
        """CREATE TABLE IF NOT EXISTS ENG_STEP (
            STEP_ID      TEXT PRIMARY KEY,
            STEP_NM      TEXT,
            STEP_GRP     TEXT,
            CRITICAL_FLAG TEXT
        )""",
        [],
        "工序定义。STEP_GRP 枚举：PHOTO/ETCH/CVD/CMP 等工艺组；CRITICAL_FLAG='Y' 为关键工序",
    ),
    "EQP_EQUIPMENT": (
        """CREATE TABLE IF NOT EXISTS EQP_EQUIPMENT (
            EQP_ID   TEXT PRIMARY KEY,
            EQP_NM   TEXT,
            EQP_TYPE TEXT,
            TOOL_GRP TEXT,
            STATUS_CD TEXT
        )""",
        [],
        "设备主档。STATUS_CD 隐性编码：R=Run,I=Idle,D=Down,M=PM保养中(算可用产能)",
    ),
    "QCS_DEFECT": (
        """CREATE TABLE IF NOT EXISTS QCS_DEFECT (
            DEFECT_ID    INTEGER PRIMARY KEY AUTOINCREMENT,
            LOT_ID       TEXT NOT NULL,
            STEP_ID      TEXT NOT NULL,
            DEFECT_CD    TEXT,
            DEFECT_CNT   INTEGER,
            INSPECT_DT   TEXT,
            DISPOSITION  TEXT
        )""",
        [("LOT_ID", "WIP_LOT.LOT_ID"), ("STEP_ID", "ENG_STEP.STEP_ID")],
        "缺陷记录。DEFECT_CD 前缀规则：P*=Particle,S*=Scratch,M*=Metal残留；DISPOSITION='SC'(Scrap)的晶圆不计入产出",
    ),
    "YLD_DAILY": (
        """CREATE TABLE IF NOT EXISTS YLD_DAILY (
            STAT_DT      TEXT,
            PRODUCT_ID   TEXT NOT NULL,
            STEP_GRP     TEXT,
            INPUT_WAFER  INTEGER,
            OUTPUT_WAFER INTEGER,
            YLD_RATE     REAL,
            PRIMARY KEY (STAT_DT, PRODUCT_ID, STEP_GRP)
        )""",
        [("PRODUCT_ID", "PRD_PRODUCT.PRODUCT_ID")],
        "日良率汇总。由夜间 job(存储过程 PKG_YLD_CALC)生成，当日08:00前查询昨日数据可能为空",
    ),
}

# seed 用常量（真实数据和隐性知识编码）
LOT_STS_VALUES = ["01", "03", "05", "07", "99"]       # 见 WIP_LOT 注释
STEP_GROUPS = ["PHOTO", "ETCH", "CVD", "CMP", "IMP", "METAL"]
EQP_STATUS = ["R", "I", "D", "M"]                      # M = PM 保养中
DEFECT_PREFIX = ["P", "S", "M"]                        # Particle/Scratch/Metal残留
DISPOSITIONS = ["SC", "RS", "OK"]                      # SC=Scrap

_PRODUCTS = [
    ("P001", "28nm Logic Chip", "28nm", 12.5, 36),
    ("P002", "22nm Logic Chip", "22nm", 9.8, 42),
    ("P003", "40nm RF Chip", "40nm", 8.2, 30),
    ("P004", "28nm RF Chip", "28nm", 7.6, 34),
    ("P005", "65nm MCU Chip", "65nm", 15.0, 22),
]

_EQPS = [
    ("E101", "Scanner-01", "LITHO", "PHOTO", "R"),
    ("E102", "Scanner-02", "LITHO", "PHOTO", "I"),
    ("E201", "Etcher-01", "ETCH", "ETCH", "R"),
    ("E202", "Etcher-02", "ETCH", "ETCH", "D"),
    ("E301", "CVD-01", "DEPOSITION", "CVD", "R"),
    ("E302", "CVD-02", "DEPOSITION", "CVD", "M"),
    ("E401", "Polisher-01", "CMP", "CMP", "R"),
    ("E402", "Polisher-02", "CMP", "CMP", "R"),
    ("E501", "IonImplant-01", "IMPLANT", "IMP", "I"),
    ("E601", "Metrology-01", "METRO", "METAL", "R"),
]

# 工序：(STEP_ID, STEP_NM, STEP_GRP, CRITICAL)
_STEPS = [
    ("S100", "PHOTO_A", "PHOTO", "Y"),
    ("S101", "PHOTO_B", "PHOTO", "N"),
    ("S200", "ETCH_A", "ETCH", "Y"),
    ("S201", "ETCH_B", "ETCH", "N"),
    ("S300", "CVD_A", "CVD", "N"),
    ("S400", "CMP_A", "CMP", "Y"),
    ("S401", "CMP_B", "CMP", "N"),
    ("S500", "IMP_A", "IMP", "N"),
    ("S600", "METAL_A", "METAL", "Y"),
]


def _gen_dates(months: int = 3) -> list[date]:
    """最近 months 个月的日期序列（含今日）。"""
    end = date.today()
    return [end - timedelta(days=i) for i in range(months * 30)]


def init_db(drop_existing: bool = False, seed_rows: int | None = None) -> sqlite3.Connection:
    """建库 + seed，幂等可重复执行。

    - drop_existing: 是否重建已存在的表和 root 索引（用于"一键重新初始化"）
    """
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    cur = conn.cursor()

    if drop_existing:
        for t in list(_SCHEMA) + ["meta_fk"]:
            cur.execute(f"DROP TABLE IF EXISTS {t}")

    # 建表
    for table, (ddl, _fk, _note) in _SCHEMA.items():
        cur.execute(ddl)

    # 清空后重新 seed（保持幂等）：先删主表再删外键引用表
    for t in ["YLD_DAILY", "QCS_DEFECT", "WIP_LOT_HIST", "PRD_ROUTE",
              "WIP_LOT", "PRD_PRODUCT", "ENG_STEP", "EQP_EQUIPMENT"]:
        cur.execute(f"DELETE FROM {t}")

    rng = random.Random(20240913)   # 固定随机种子，保证演示数据可复现
    today = date.today()

    # --- 产品、工序、设备（主档）---
    cur.executemany("INSERT INTO PRD_PRODUCT VALUES (?,?,?,?,?)", _PRODUCTS)
    cur.executemany("INSERT INTO ENG_STEP VALUES (?,?,?,?)", _STEPS)
    cur.executemany("INSERT INTO EQP_EQUIPMENT VALUES (?,?,?,?,?)", _EQPS)

    # --- 路线：每个产品 6~9 道工序 ---
    routes = []
    for prod_id, *_ in _PRODUCTS:
        seq = 0
        for step_id, *_ in _STEPS[::3]:   # 采样 S100,S400,S600 等
            seq += 1
            routes.append((prod_id, seq, step_id))
    cur.executemany("INSERT INTO PRD_ROUTE (PRODUCT_ID, STEP_SEQ, STEP_ID) VALUES (?,?,?)", routes)

    # --- 在制批次 WIP_LOT ---
    lots: list[tuple] = []
    lot_pool = 45                      # 每产品批次数
    today_iso = today.isoformat()
    for p_idx, (prod_id, *_ ) in enumerate(_PRODUCTS):
        for i in range(lot_pool):
            lot_id = f"FP{20240913 % 1000000 + p_idx * lot_pool + i + 1}"
            sts_dist = ["01", "03", "05", "03", "03", "03", "07", "99"]
            lot_sts = rng.choice(sts_dist)
            create_dt = today_iso if rng.random() < 0.3 else (today - timedelta(days=rng.randint(1, 90))).isoformat()
            stage = _STEPS[p_idx % len(_STEPS)][0]
            lots.append((
                lot_id, prod_id, stage, lot_sts,
                rng.randint(20, 25), rng.randint(1, 25),
                create_dt, today_iso,
            ))
    cur.executemany(
        "INSERT INTO WIP_LOT VALUES (?,?,?,?,?,?,?,?)", lots)

    # --- 过站历史 WIP_LOT_HIST ---
    hist_rows = []
    for lot_id, *_ in lots:
        n = rng.randint(2, 6)
        steps_done = rng.sample(_STEPS, min(n, len(_STEPS)))
        for step_id, *_ in steps_done:
            eqp = rng.choice(_EQPS)[0]
            track_out = (today - timedelta(days=rng.randint(0, 90))).isoformat()
            hist_rows.append((lot_id, step_id, eqp, track_out,
                              rng.randint(1, 25), rng.randint(0, 8)))
    cur.executemany(
        "INSERT INTO WIP_LOT_HIST (LOT_ID, STEP_ID, EQP_ID, TRACK_OUT_DT, QTY_OUT, DEFECT_CNT) "
        "VALUES (?,?,?,?,?,?)", hist_rows)

    # --- 日良率 YLD_DAILY（夜间 job 产物，最近 90 天）---
    yld_rows = []
    for days in range(1, 91):
        stat_dt = (today - timedelta(days=days)).isoformat()
        for (prod_id, *_), step_grp in zip(_PRODUCTS, STEP_GROUPS[:len(_PRODUCTS)]):
            input_w = rng.randint(40, 90)
            # 良率受工艺组影响，并叠加噪声
            base = {"PHOTO": 0.96, "ETCH": 0.93, "CVD": 0.95, "CMP": 0.94,
                    "IMP": 0.97, "METAL": 0.96}[step_grp]
            yld = max(0.75, min(1.0, base + rng.uniform(-0.05, 0.03)))
            output_w = int(input_w * yld)
            yld_rows.append((stat_dt, prod_id, step_grp, input_w, output_w, round(yld, 4)))
    cur.executemany(
        "INSERT INTO YLD_DAILY VALUES (?,?,?,?,?,?)", yld_rows)

    # --- 缺陷 QCS_DEFECT ---
    defect_rows = []
    for lot_id, *_ in lots:
        if rng.random() < 0.5:   # 一半批次有缺陷记录
            step = rng.choice(_STEPS)
            prefix = rng.choice(DEFECT_PREFIX)
            defect_cd = rng.choice([f"{prefix}0{rng.randint(1,5)}", f"{prefix}{rng.randint(10,20)}"])
            disp = rng.choice(DISPOSITIONS)
            defect_rows.append((lot_id, step[0], defect_cd, rng.randint(1, 30),
                                (today - timedelta(days=rng.randint(0, 90))).isoformat(), disp))
    cur.executemany(
        "INSERT INTO QCS_DEFECT (LOT_ID, STEP_ID, DEFECT_CD, DEFECT_CNT, INSPECT_DT, DISPOSITION) "
        "VALUES (?,?,?,?,?,?)", defect_rows)

    # --- 外键元数据表 meta_fk：提取器据此生成血缘 ---
    cur.execute("DROP TABLE IF EXISTS meta_fk")
    cur.execute("""CREATE TABLE meta_fk (
            FK_COL   TEXT, SRC_TABLE TEXT, TGT_TABLE TEXT, TGT_COL TEXT)""")
    fk_rows = []
    for table, (_ddl, fk_list, _note) in _SCHEMA.items():
        for (col, target) in fk_list:
            tgt_tbl, tgt_col = target.split(".")
            fk_rows.append((col, table, tgt_tbl, tgt_col))
    cur.executemany("INSERT INTO meta_fk VALUES (?,?,?,?)", fk_rows)

    # 为 temp 状态/种子批次计数污染：创建干净的 seed 汇总视图（可选）
    conn.commit()
    return conn


def table_names() -> list[str]:
    """返回业务表名列表（按 seed 顺序）。"""
    return list(_SCHEMA.keys())


def get_meta_fk(conn: sqlite3.Connection) -> list[tuple[str, str, str, str]]:
    """读取外键元数据：(FK列, 源表, 目标表, 目标列)。"""
    rows = conn.execute("SELECT FK_COL, SRC_TABLE, TGT_TABLE, TGT_COL FROM meta_fk").fetchall()
    return [(r[0], r[1], r[2], r[3]) for r in rows]


def row_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _digest(seed: int) -> str:
    return hashlib.md5(str(seed).encode()).hexdigest()[:8]


def seed_hash(conn: sqlite3.Connection) -> str:
    """用于幂等/版本标记（可选）。"""
    return _digest(sum(row_count(conn, t) for t in table_names()))
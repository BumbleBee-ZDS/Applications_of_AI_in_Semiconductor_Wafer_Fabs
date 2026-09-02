"""
FabCapacityAgent - 数据库管理模块

封装SQLite连接管理、表结构初始化、通用CRUD基类。
所有DB操作统一走 try-except 兜底, 配合 logger 输出错误。
"""

import sqlite3
import threading
import datetime as dt
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

import pandas as pd

# 工具模块
from utils.helpers import (
    get_logger,
    resolve_path,
    ensure_dir,
    get_config,
    try_except,
    now,
)
from utils.constants import (
    TABLE_EQUIPMENT,
    TABLE_LOTS,
    TABLE_LOT_HISTORY,
    TABLE_EQUIPMENT_EVENTS,
    TABLE_DAILY_OUTPUT,
    TABLE_AGENT_LOGS,
)

logger = get_logger("Database", level="INFO")

# =============================================================================
# 连接管理 (单例 + 线程锁)
# =============================================================================

class DatabaseManager:
    """
    SQLite数据库管理器,负责:
      1) 统一打开/关闭连接,保证线程安全
      2) 首次使用时建表(DDL)
      3) 提供事务上下文管理器 + DataFrame读写便捷方法
    """

    _instance: Optional["DatabaseManager"] = None
    _init_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "DatabaseManager":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance

    def __init__(self, db_path: Optional[str] = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self._db_path: str = db_path or get_config("database", "path", default="data/fab_capacity.db")
        self._abs_path = resolve_path(self._db_path)
        ensure_dir(self._abs_path.parent)
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = True

        # 延迟连接,首次调用 get_connection 时再真正打开
        logger.info(f"DatabaseManager 就绪, DB路径: {self._abs_path}")

    # ---------------------------------------------------------------- 连接
    @property
    def path(self) -> str:
        return str(self._abs_path)

    def get_connection(self) -> sqlite3.Connection:
        """
        获取当前连接,若关闭或未创建则重新打开,并开启外键约束。
        线程安全。
        """
        with self._lock:
            if self._conn is None:
                try:
                    self._conn = sqlite3.connect(
                        self._abs_path,
                        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                        check_same_thread=False,  # 自行加锁,允许跨线程
                        timeout=30,
                        isolation_level=None,  # 自动commit模式,事务由begin()手动控制
                    )
                    self._conn.execute("PRAGMA foreign_keys = ON")
                    self._conn.execute("PRAGMA journal_mode = WAL")      # 高并发读
                    self._conn.execute("PRAGMA synchronous = NORMAL")
                    self._conn.row_factory = sqlite3.Row
                except sqlite3.Error as exc:
                    logger.error(f"打开数据库失败: {exc}")
                    raise
            return self._conn

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except sqlite3.Error as exc:
                    logger.warning(f"关闭数据库异常: {exc}")
                finally:
                    self._conn = None

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """
        显式事务上下文管理器。
        用法:
            with db.transaction() as conn:
                conn.execute(...)
        """
        conn = self.get_connection()
        with self._lock:
            try:
                conn.execute("BEGIN")
                yield conn
                conn.execute("COMMIT")
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                logger.error(f"事务回滚: {exc}")
                raise

    # ---------------------------------------------------------------- DDL
    def initialize_schema(self, force: bool = False) -> None:
        """
        创建所有业务表。已存在则跳过(除非 force=True 会先DROP)。
        """
        logger.info("初始化数据库表结构...")
        with self.transaction() as conn:
            if force:
                for tbl in [TABLE_AGENT_LOGS, TABLE_LOT_HISTORY, TABLE_EQUIPMENT_EVENTS,
                            TABLE_DAILY_OUTPUT, TABLE_LOTS, TABLE_EQUIPMENT]:
                    conn.execute(f"DROP TABLE IF EXISTS {tbl}")

            # 1) equipment 设备主数据
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_EQUIPMENT} (
                    equip_id      TEXT PRIMARY KEY,
                    equip_type    TEXT NOT NULL,              -- Scanner/Etcher/...
                    process       TEXT NOT NULL,              -- PHOTO/ETCH/...
                    status        TEXT NOT NULL DEFAULT 'IDLE',
                    model         TEXT,
                    install_date  TIMESTAMP,
                    location      TEXT,
                    total_run_hours REAL DEFAULT 0,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_eq_process ON {TABLE_EQUIPMENT}(process)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_eq_status  ON {TABLE_EQUIPMENT}(status)")

            # 2) lots 批次主表
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_LOTS} (
                    lot_id        TEXT PRIMARY KEY,
                    product_type  TEXT NOT NULL,              -- Logic_A/Logic_B/Memory_C
                    wafers_count  INTEGER NOT NULL DEFAULT 25,
                    priority      INTEGER DEFAULT 1,
                    start_time    TIMESTAMP,                  -- 入厂时间
                    end_time      TIMESTAMP,                  -- 出厂时间(完工)
                    current_step  INTEGER DEFAULT 0,          -- 当前工序索引
                    current_process TEXT,                     -- 当前工序代码
                    status        TEXT NOT NULL DEFAULT 'WIP', -- WIP/DONE/HOLD/SCRAP
                    yield_rate    REAL DEFAULT 1.0,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_lot_product ON {TABLE_LOTS}(product_type)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_lot_status  ON {TABLE_LOTS}(status)")

            # 3) lot_history 工序历史(每批每道工序一条)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_LOT_HISTORY} (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    lot_id        TEXT NOT NULL,
                    process       TEXT NOT NULL,
                    step_index    INTEGER NOT NULL,
                    equip_id      TEXT,
                    start_time    TIMESTAMP NOT NULL,
                    end_time      TIMESTAMP,
                    input_qty     INTEGER,
                    output_qty    INTEGER,
                    scrap_qty     INTEGER DEFAULT 0,
                    wait_time_h   REAL DEFAULT 0,
                    process_time_h REAL DEFAULT 0,
                    status        TEXT DEFAULT 'DONE',        -- RUN/HOLD/DONE/SKIP
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(lot_id) REFERENCES {TABLE_LOTS}(lot_id),
                    FOREIGN KEY(equip_id) REFERENCES {TABLE_EQUIPMENT}(equip_id)
                )
            """)
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_lh_lot ON {TABLE_LOT_HISTORY}(lot_id)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_lh_process ON {TABLE_LOT_HISTORY}(process)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_lh_start   ON {TABLE_LOT_HISTORY}(start_time)")

            # 4) equipment_events 设备事件(启停/故障/PM)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_EQUIPMENT_EVENTS} (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id      TEXT UNIQUE,
                    equip_id      TEXT NOT NULL,
                    event_type    TEXT NOT NULL,              -- LOT_START/EQUIP_DOWN/PM_START/...
                    event_time    TIMESTAMP NOT NULL,
                    end_time      TIMESTAMP,
                lot_id        TEXT,
                    duration_h    REAL DEFAULT 0,
                    reason        TEXT,
                    detail        TEXT,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(equip_id) REFERENCES {TABLE_EQUIPMENT}(equip_id)
                )
            """)
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_ee_equip ON {TABLE_EQUIPMENT_EVENTS}(equip_id)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_ee_time  ON {TABLE_EQUIPMENT_EVENTS}(event_time)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_ee_type  ON {TABLE_EQUIPMENT_EVENTS}(event_type)")

            # 5) daily_output 日产出汇总(供预测/报表快速读)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_DAILY_OUTPUT} (
                    stat_date     DATE PRIMARY KEY,
                    product_type  TEXT DEFAULT 'ALL',
                    output_wafers INTEGER DEFAULT 0,
                    move_count    INTEGER DEFAULT 0,
                    completed_lots INTEGER DEFAULT 0,
                    avg_oee       REAL DEFAULT 0,
                    avg_cycle_time_h REAL DEFAULT 0,
                    scrap_count   INTEGER DEFAULT 0,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stat_date, product_type)
                )
            """)

            # 6) agent_logs Agent执行日志(编排器记录每步输入输出)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_AGENT_LOGS} (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id        TEXT NOT NULL,
                    agent_type    TEXT NOT NULL,
                    stage         TEXT,                         -- perceive/think/act
                    status        TEXT DEFAULT 'success',       -- success/failed/timeout
                    input_snapshot TEXT,                         -- JSON
                    output_result  TEXT,                         -- JSON
                    duration_ms   INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_ag_run ON {TABLE_AGENT_LOGS}(run_id)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_ag_agent ON {TABLE_AGENT_LOGS}(agent_type)")

        logger.info("数据库表结构初始化完成 ✓")

    # ---------------------------------------------------------------- CRUD
    @try_except(default_return=None)
    def execute(self, sql: str, params: Iterable[Any] = ()) -> Optional[int]:
        """
        执行一条写SQL(INSERT/UPDATE/DELETE),返回lastrowid或affected rows。
        """
        with self._lock:
            conn = self.get_connection()
            cur = conn.execute(sql, tuple(params))
            return cur.lastrowid or cur.rowcount

    @try_except(default_return=[])
    def query(self, sql: str, params: Iterable[Any] = ()) -> List[sqlite3.Row]:
        """执行一条SELECT,返回Row列表。"""
        with self._lock:
            conn = self.get_connection()
            cur = conn.execute(sql, tuple(params))
            return cur.fetchall()

    @try_except(default_return=None)
    def query_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
        """查询首行,找不到返回None。"""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @try_except(default_return=pd.DataFrame())
    def query_df(self, sql: str, params: Iterable[Any] = ()) -> pd.DataFrame:
        """查询并返回DataFrame,空数据返回空DF。"""
        with self._lock:
            conn = self.get_connection()
            return pd.read_sql_query(sql, conn, params=tuple(params))

    @try_except(default_return=-1)
    def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> int:
        """
        批量插入字典列表,字段自动对齐。
        返回实际插入条数(失败时返回-1)。
        """
        if not rows:
            return 0
        columns = list(rows[0].keys())
        placeholders = ",".join(["?"] * len(columns))
        col_sql = ",".join(f'"{c}"' for c in columns)
        sql = f'INSERT OR REPLACE INTO "{table}" ({col_sql}) VALUES ({placeholders})'
        values = [tuple(r.get(c) for c in columns) for r in rows]
        with self.transaction() as conn:
            cur = conn.executemany(sql, values)
            return cur.rowcount or len(values)

    @try_except(default_return=None)
    def write_df(self, table: str, df: pd.DataFrame, if_exists: str = "append") -> None:
        """将DataFrame写入指定表,通过pandas to_sql。"""
        if df is None or df.empty:
            return
        with self._lock:
            conn = self.get_connection()
            df.to_sql(table, conn, if_exists=if_exists, index=False)

    # ---------------------------------------------------------------- 便捷统计
    @try_except(default_return=0)
    def count(self, table: str, where: str = "1=1", params: Iterable[Any] = ()) -> int:
        row = self.query_one(f"SELECT COUNT(*) AS c FROM {table} WHERE {where}", params)
        return int(row["c"]) if row else 0


# =============================================================================
# 便捷导出: get_db() 单例
# =============================================================================

def get_db(db_path: Optional[str] = None) -> DatabaseManager:
    """获取全局单例数据库管理器。"""
    return DatabaseManager(db_path=db_path)


# =============================================================================
# 模块自检
# =============================================================================

if __name__ == "__main__":
    db = get_db()
    db.initialize_schema()
    print("表列表:")
    r = db.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for row in r:
        print(" -", row["name"], f"({db.count(row['name'])} 行)")

"""
FabCapacityAgent - 批次/晶圆/工序历史 数据模型 & DAO

Lot       -> 批次 (25片Wafer)
LotStep   -> 批次历史中的一步工序记录
LotsDAO   -> 对lots/lot_history两张表的封装查询/写入
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import datetime as dt

import pandas as pd

from .database import get_db, DatabaseManager
from utils.helpers import (
    try_except,
    generate_id,
    parse_datetime,
    get_logger,
    hours_between,
)
from utils.constants import (
    TABLE_LOTS,
    TABLE_LOT_HISTORY,
    PRODUCT_LOGIC_A,
    ALL_PRODUCTS,
)

logger = get_logger("WaferModel")

# =============================================================================
# dataclass 定义
# =============================================================================

@dataclass
class Lot:
    """批次(25片晶圆为一批)。"""
    lot_id: str
    product_type: str
    wafers_count: int = 25
    priority: int = 1
    start_time: Optional[dt.datetime] = None
    end_time: Optional[dt.datetime] = None
    current_step: int = 0
    current_process: Optional[str] = None
    status: str = "WIP"     # WIP(在制) / DONE(完工) / HOLD(冻结) / SCRAP(报废)
    yield_rate: float = 1.0

    def to_row(self) -> Dict[str, Any]:
        """转DB可写字典,datetime自动转字符串存。"""
        d = asdict(self)
        for k in ("start_time", "end_time"):
            v = d.get(k)
            if isinstance(v, dt.datetime):
                d[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class LotStep:
    """批次在某一道工序上的处理记录(一行lot_history)。"""
    lot_id: str
    process: str
    step_index: int
    equip_id: Optional[str] = None
    start_time: Optional[dt.datetime] = None
    end_time: Optional[dt.datetime] = None
    input_qty: int = 25
    output_qty: int = 25
    scrap_qty: int = 0
    wait_time_h: float = 0.0
    process_time_h: float = 0.0
    status: str = "DONE"   # RUN / HOLD / DONE / SKIP

    def to_row(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ("start_time", "end_time"):
            v = d.get(k)
            if isinstance(v, dt.datetime):
                d[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return d


# =============================================================================
# DAO
# =============================================================================

class LotsDAO:
    """批次/工序历史 DAO,封装所有SQL查询。"""

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or get_db()

    # --------------------------------------------------------- 写入
    @try_except(default_return=False)
    def insert_lot(self, lot: Lot) -> bool:
        row = lot.to_row()
        return self.db.insert_many(TABLE_LOTS, [row]) == 1

    @try_except(default_return=0)
    def bulk_insert_lots(self, lots: List[Lot]) -> int:
        if not lots:
            return 0
        return self.db.insert_many(TABLE_LOTS, [l.to_row() for l in lots])

    @try_except(default_return=0)
    def bulk_insert_steps(self, steps: List[LotStep]) -> int:
        if not steps:
            return 0
        return self.db.insert_many(TABLE_LOT_HISTORY, [s.to_row() for s in steps])

    # --------------------------------------------------------- 查询
    @try_except(default_return=pd.DataFrame())
    def list_active_wip(self, as_df: bool = True):
        """
        查询当前所有在制品(WIP)批次。返回DataFrame或Lot列表。
        """
        sql = f"""
            SELECT * FROM {TABLE_LOTS}
            WHERE status = 'WIP'
            ORDER BY priority DESC, start_time ASC
        """
        df = self.db.query_df(sql)
        if as_df:
            return df
        return [self._row_to_lot(r) for r in self.db.query(sql)]

    @try_except(default_return=pd.DataFrame())
    def list_steps_by_lot(self, lot_id: str) -> pd.DataFrame:
        """查询指定批次所有工序历史,按step_index排序。"""
        sql = f"""
            SELECT * FROM {TABLE_LOT_HISTORY}
            WHERE lot_id = ? ORDER BY step_index ASC
        """
        return self.db.query_df(sql, (lot_id,))

    @try_except(default_return=pd.DataFrame())
    def list_steps_between(self, start_time: Any, end_time: Any, process: Optional[str] = None) -> pd.DataFrame:
        """按时间窗口查询所有工序记录(可过滤工序)。"""
        sql = f"""
            SELECT lh.*, l.product_type, l.wafers_count
            FROM {TABLE_LOT_HISTORY} lh
            JOIN {TABLE_LOTS} l ON l.lot_id = lh.lot_id
            WHERE lh.start_time >= ? AND lh.start_time < ?
        """
        params: List[Any] = [
            parse_datetime(start_time) or dt.datetime(2000, 1, 1),
            parse_datetime(end_time) or dt.datetime(2100, 1, 1),
        ]
        if process:
            sql += " AND lh.process = ?"
            params.append(process)
        sql += " ORDER BY lh.start_time ASC"
        return self.db.query_df(sql, params)

    @try_except(default_return=0)
    def count_wip(self, process: Optional[str] = None) -> int:
        """统计WIP批数(可按当前工序过滤)。"""
        sql = f"SELECT COUNT(*) AS c FROM {TABLE_LOTS} WHERE status='WIP'"
        params: List[Any] = []
        if process:
            sql += " AND current_process = ?"
            params.append(process)
        row = self.db.query_one(sql, params)
        return int(row["c"]) if row else 0

    @try_except(default_return=0)
    def wip_wafers(self, process: Optional[str] = None) -> int:
        """统计WIP晶圆片数。"""
        sql = f"SELECT COALESCE(SUM(wafers_count),0) AS s FROM {TABLE_LOTS} WHERE status='WIP'"
        params: List[Any] = []
        if process:
            sql += " AND current_process = ?"
            params.append(process)
        row = self.db.query_one(sql, params)
        return int(row["s"]) if row else 0

    @try_except(default_return=pd.DataFrame())
    def wip_distribution(self) -> pd.DataFrame:
        """
        返回按工序分组的WIP分布 DataFrame:
        columns: process, lots, wafers
        """
        sql = f"""
            SELECT
                COALESCE(current_process, 'NOT_STARTED') AS process,
                COUNT(*)           AS lots,
                SUM(wafers_count)  AS wafers
            FROM {TABLE_LOTS}
            WHERE status = 'WIP'
            GROUP BY COALESCE(current_process, 'NOT_STARTED')
            ORDER BY wafers DESC
        """
        return self.db.query_df(sql)

    @try_except(default_return=pd.DataFrame())
    def completed_lots_between(self, start_time: Any, end_time: Any) -> pd.DataFrame:
        """统计时间区间内完工的批次。"""
        sql = f"""
            SELECT * FROM {TABLE_LOTS}
            WHERE status='DONE'
              AND end_time IS NOT NULL
              AND end_time >= ?
              AND end_time < ?
            ORDER BY end_time ASC
        """
        return self.db.query_df(sql, (
            parse_datetime(start_time),
            parse_datetime(end_time),
        ))

    @try_except(default_return=None)
    def get_lot(self, lot_id: str) -> Optional[Lot]:
        row = self.db.query_one(f"SELECT * FROM {TABLE_LOTS} WHERE lot_id=?", (lot_id,))
        return self._row_to_lot(row) if row else None

    # --------------------------------------------------------- 更新
    @try_except(default_return=False)
    def update_lot_status(self, lot_id: str, status: str, **fields) -> bool:
        """更新批次状态/进度。支持传入额外字段更新current_step/current_process等。"""
        allowed = {"status", "current_step", "current_process", "end_time", "yield_rate"}
        sets = ["status = ?"]
        params: List[Any] = [status]
        for k, v in fields.items():
            if k in allowed:
                if isinstance(v, dt.datetime):
                    v = v.strftime("%Y-%m-%d %H:%M:%S")
                sets.append(f"{k} = ?")
                params.append(v)
        sets.append("updated_at = CURRENT_TIMESTAMP")
        params.append(lot_id)
        sql = f"UPDATE {TABLE_LOTS} SET {', '.join(sets)} WHERE lot_id=?"
        return self.db.execute(sql, params) is not None

    # --------------------------------------------------------- 内部
    @staticmethod
    def _row_to_lot(r: Any) -> Lot:
        return Lot(
            lot_id=r["lot_id"],
            product_type=r["product_type"],
            wafers_count=int(r["wafers_count"] or 25),
            priority=int(r["priority"] or 1),
            start_time=parse_datetime(r["start_time"]),
            end_time=parse_datetime(r["end_time"]),
            current_step=int(r["current_step"] or 0),
            current_process=r["current_process"],
            status=r["status"] or "WIP",
            yield_rate=float(r["yield_rate"] or 1.0),
        )


# =============================================================================
# 便捷构造函数
# =============================================================================

def make_lot(
    product_type: str = PRODUCT_LOGIC_A,
    wafers_count: int = 25,
    start_time: Optional[dt.datetime] = None,
    seq: Optional[int] = None,
) -> Lot:
    """生成一个Lot实例,lot_id自动编号。"""
    if product_type not in ALL_PRODUCTS:
        logger.warning(f"未知产品类型: {product_type}, 回退为 {PRODUCT_LOGIC_A}")
        product_type = PRODUCT_LOGIC_A
    return Lot(
        lot_id=generate_id("LOT", seq=seq),
        product_type=product_type,
        wafers_count=wafers_count,
        priority=1,
        start_time=start_time or dt.datetime.now(),
    )

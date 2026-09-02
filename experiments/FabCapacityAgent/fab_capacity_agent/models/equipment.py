"""
FabCapacityAgent - 设备模型 & DAO

Equipment      -> 设备主数据(120台设备)
EquipmentEvent -> 设备事件(故障/PM/换型等)
EquipmentDAO   -> 对equipment/equipment_events两张表的封装CRUD
"""

from dataclasses import dataclass, asdict
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
    TABLE_EQUIPMENT,
    TABLE_EQUIPMENT_EVENTS,
    ALL_EQUIP_STATUSES,
    EQUIP_STATUS_IDLE,
    EQUIP_STATUS_RUN,
    EQUIP_STATUS_DOWN,
    EQUIP_STATUS_PM,
    EQUIP_STATUS_SETUP,
    EVENT_EQUIP_DOWN,
    EVENT_EQUIP_RECOVER,
    EVENT_PM_START,
    EVENT_PM_END,
    EVENT_SETUP_START,
    EVENT_SETUP_END,
    EVENT_LOT_START,
    EVENT_LOT_COMPLETE,
)

logger = get_logger("EquipmentModel")

# =============================================================================
# dataclass
# =============================================================================

@dataclass
class Equipment:
    """设备主数据。"""
    equip_id: str
    equip_type: str
    process: str
    status: str = EQUIP_STATUS_IDLE
    model: Optional[str] = None
    install_date: Optional[dt.datetime] = None
    location: Optional[str] = None
    total_run_hours: float = 0.0

    def to_row(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(d.get("install_date"), dt.datetime):
            d["install_date"] = d["install_date"].strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class EquipmentEvent:
    """设备事件(状态转换/故障/PM/换型/生产批次)。"""
    equip_id: str
    event_type: str
    event_time: dt.datetime
    event_id: Optional[str] = None
    end_time: Optional[dt.datetime] = None
    lot_id: Optional[str] = None
    duration_h: float = 0.0
    reason: Optional[str] = None
    detail: Optional[str] = None

    def __post_init__(self):
        # event_id 未显式指定则自动生成
        if self.event_id is None:
            self.event_id = generate_id("EVT")

    def to_row(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ("event_time", "end_time"):
            v = d.get(k)
            if isinstance(v, dt.datetime):
                d[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        return d


# =============================================================================
# DAO
# =============================================================================

class EquipmentDAO:
    """设备/设备事件 CRUD DAO。"""

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or get_db()

    # --------------------------------------------------------- 写入
    @try_except(default_return=0)
    def bulk_insert_equipment(self, equips: List[Equipment]) -> int:
        if not equips:
            return 0
        return self.db.insert_many(TABLE_EQUIPMENT, [e.to_row() for e in equips])

    @try_except(default_return=0)
    def bulk_insert_events(self, events: List[EquipmentEvent]) -> int:
        if not events:
            return 0
        return self.db.insert_many(TABLE_EQUIPMENT_EVENTS, [e.to_row() for e in events])

    @try_except(default_return=False)
    def update_status(self, equip_id: str, status: str, run_hours_inc: float = 0.0) -> bool:
        if status not in ALL_EQUIP_STATUSES:
            logger.warning(f"无效设备状态: {status}, 丢弃更新")
            return False
        sql = f"""
            UPDATE {TABLE_EQUIPMENT}
            SET status = ?,
                total_run_hours = total_run_hours + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE equip_id = ?
        """
        return self.db.execute(sql, (status, float(run_hours_inc), equip_id)) is not None

    # --------------------------------------------------------- 查询
    @try_except(default_return=pd.DataFrame())
    def list_equipment(self, process: Optional[str] = None, status: Optional[str] = None) -> pd.DataFrame:
        """查询设备列表,可选按工序/状态过滤。"""
        sql = f"SELECT * FROM {TABLE_EQUIPMENT} WHERE 1=1"
        params: List[Any] = []
        if process:
            sql += " AND process = ?"
            params.append(process)
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY process, equip_id"
        return self.db.query_df(sql, params)

    @try_except(default_return=[])
    def list_equipment_by_process(self, process: str, statuses: Optional[List[str]] = None) -> List[Equipment]:
        """获取指定工序的设备对象列表,方便批量调度。"""
        sql = f"SELECT * FROM {TABLE_EQUIPMENT} WHERE process = ?"
        params: List[Any] = [process]
        if statuses:
            ph = ",".join("?" for _ in statuses)
            sql += f" AND status IN ({ph})"
            params.extend(statuses)
        return [self._row_to_equip(r) for r in self.db.query(sql, params)]

    @try_except(default_return=None)
    def get_equipment(self, equip_id: str) -> Optional[Equipment]:
        row = self.db.query_one(f"SELECT * FROM {TABLE_EQUIPMENT} WHERE equip_id=?", (equip_id,))
        return self._row_to_equip(row) if row else None

    @try_except(default_return=pd.DataFrame())
    def status_summary(self) -> pd.DataFrame:
        """按工序×状态 聚合统计数量。"""
        sql = f"""
            SELECT process, status, COUNT(*) AS cnt
            FROM {TABLE_EQUIPMENT}
            GROUP BY process, status
            ORDER BY process, status
        """
        return self.db.query_df(sql)

    @try_except(default_return=pd.DataFrame())
    def events_between(self, start_time: Any, end_time: Any,
                        equip_id: Optional[str] = None,
                        event_type: Optional[str] = None) -> pd.DataFrame:
        sql = f"""
            SELECT * FROM {TABLE_EQUIPMENT_EVENTS}
            WHERE event_time >= ? AND event_time < ?
        """
        params: List[Any] = [
            parse_datetime(start_time) or dt.datetime(2000, 1, 1),
            parse_datetime(end_time) or dt.datetime(2100, 1, 1),
        ]
        if equip_id:
            sql += " AND equip_id = ?"
            params.append(equip_id)
        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)
        sql += " ORDER BY event_time ASC"
        return self.db.query_df(sql, params)

    @try_except(default_return=pd.DataFrame())
    def downtime_events(self, start_time: Any, end_time: Any) -> pd.DataFrame:
        """
        拉取 DOWN / PM / SETUP 开始结束事件,方便帕累托分析。
        """
        sql = f"""
            SELECT ee.*, eq.process
            FROM {TABLE_EQUIPMENT_EVENTS} ee
            JOIN {TABLE_EQUIPMENT} eq ON eq.equip_id = ee.equip_id
            WHERE ee.event_time >= ? AND ee.event_time < ?
              AND ee.event_type IN (
                '{EVENT_EQUIP_DOWN}','{EVENT_EQUIP_RECOVER}',
                '{EVENT_PM_START}','{EVENT_PM_END}',
                '{EVENT_SETUP_START}','{EVENT_SETUP_END}'
              )
            ORDER BY ee.event_time ASC
        """
        return self.db.query_df(sql, (
            parse_datetime(start_time),
            parse_datetime(end_time),
        ))

    # --------------------------------------------------------- 内部
    @staticmethod
    def _row_to_equip(r: Any) -> Equipment:
        return Equipment(
            equip_id=r["equip_id"],
            equip_type=r["equip_type"],
            process=r["process"],
            status=r["status"] or EQUIP_STATUS_IDLE,
            model=r["model"],
            install_date=parse_datetime(r["install_date"]),
            location=r["location"],
            total_run_hours=float(r["total_run_hours"] or 0.0),
        )


# =============================================================================
# 便捷构造
# =============================================================================

def make_equipment(
    equip_id: str,
    equip_type: str,
    process: str,
    status: str = EQUIP_STATUS_IDLE,
    model: Optional[str] = None,
    location: Optional[str] = None,
) -> Equipment:
    """构建设备对象。"""
    return Equipment(
        equip_id=equip_id,
        equip_type=equip_type,
        process=process,
        status=status,
        model=model or f"{equip_type}-STD",
        location=location or f"BAY-{process[-1]}",
    )

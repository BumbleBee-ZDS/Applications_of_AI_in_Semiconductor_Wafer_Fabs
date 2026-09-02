"""
FabCapacityAgent - 产能指标 & 日产出 模型 & DAO

CapacitySnapshot -> 结构化的产能快照(Agent输入)
DailyOutputDAO   -> daily_output表CRUD + 预定义KPI快速查询
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional
import datetime as dt
import json

import pandas as pd

from .database import get_db, DatabaseManager
from utils.helpers import (
    try_except,
    parse_datetime,
    get_logger,
    safe_round,
)
from utils.constants import (
    TABLE_DAILY_OUTPUT,
    TABLE_AGENT_LOGS,
    ALL_PROCESSES,
)

logger = get_logger("CapacityModel")

# =============================================================================
# dataclass 定义: 快照 / 指标组
# =============================================================================

@dataclass
class ProcessKPI:
    """单个工序维度的KPI结构。"""
    process: str
    equipment_count: int = 0
    utilization: float = 0.0       # 0~1
    availability: float = 0.0
    performance: float = 0.0
    quality: float = 0.0
    oee: float = 0.0
    uph: float = 0.0               # 每小时产出(片)
    wip_wafers: int = 0
    avg_cycle_time_h: float = 0.0
    is_bottleneck: bool = False
    bottleneck_rate: float = 0.0


@dataclass
class CapacitySnapshot:
    """
    全厂产能状态快照(PerceptionAgent的标准输出)。
    所有字段均为结构化数值,便于后续分析/决策Agent消费。
    """
    snapshot_time: dt.datetime = field(default_factory=lambda: dt.datetime.now())

    # --- 全厂级KPI ---
    overall_oee: float = 0.0
    overall_availability: float = 0.0
    overall_performance: float = 0.0
    overall_quality: float = 0.0
    total_uph: float = 0.0
    wip_total_wafers: int = 0
    wip_total_lots: int = 0
    daily_output_24h: int = 0
    completed_lots_24h: int = 0
    avg_cycle_time_h: float = 0.0
    total_move_24h: int = 0

    # --- 工序级KPI (key=process代码) ---
    by_process: Dict[str, ProcessKPI] = field(default_factory=dict)

    # --- 瓶颈排名 (list of process code, 按严重度降序) ---
    bottleneck_rank: List[str] = field(default_factory=list)

    # --- 标签(供LLM理解) ---
    extra: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------- 工具
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["snapshot_time"] = self.snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def pretty_summary(self) -> str:
        """快速文本摘要(写入报告/展示用)。"""
        lines = [
            f"📸 产能快照 @ {self.snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"· 全厂OEE: {safe_round(self.overall_oee*100,2)}%",
            f"· 24h产出: {self.daily_output_24h}片 / 完成{self.completed_lots_24h}批",
            f"· WIP总量: {self.wip_total_wafers}片 / {self.wip_total_lots}批",
            f"· 平均CycleTime: {safe_round(self.avg_cycle_time_h,1)}h",
            f"· 瓶颈工序Top3: {' → '.join(self.bottleneck_rank[:3]) or '无'}",
        ]
        return "\n".join(lines)


@dataclass
class DailyOutputRow:
    """daily_output 表一行。"""
    stat_date: dt.date
    product_type: str = "ALL"
    output_wafers: int = 0
    move_count: int = 0
    completed_lots: int = 0
    avg_oee: float = 0.0
    avg_cycle_time_h: float = 0.0
    scrap_count: int = 0

    def to_row(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(d.get("stat_date"), (dt.date, dt.datetime)):
            d["stat_date"] = d["stat_date"].strftime("%Y-%m-%d")
        return d


# =============================================================================
# DAO
# =============================================================================

class DailyOutputDAO:
    """日产出汇总表DAO(查询/写入/聚合)。"""

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or get_db()

    # --------------------------------------------------------- 写入
    @try_except(default_return=0)
    def upsert_rows(self, rows: List[DailyOutputRow]) -> int:
        if not rows:
            return 0
        return self.db.insert_many(TABLE_DAILY_OUTPUT, [r.to_row() for r in rows])

    # --------------------------------------------------------- 查询
    @try_except(default_return=pd.DataFrame())
    def between(self, start_date: Any, end_date: Any,
                product_type: str = "ALL") -> pd.DataFrame:
        """
        读取指定日期范围(含首尾)的日产出DataFrame,按日期升序。
        缺日期自动补零行,保证时序连续。
        """
        s = parse_datetime(start_date)
        e = parse_datetime(end_date)
        if s is None or e is None:
            return pd.DataFrame()
        sql = f"""
            SELECT * FROM {TABLE_DAILY_OUTPUT}
            WHERE product_type = ?
              AND stat_date >= ? AND stat_date <= ?
            ORDER BY stat_date ASC
        """
        df = self.db.query_df(sql, (
            product_type,
            s.strftime("%Y-%m-%d"),
            e.strftime("%Y-%m-%d"),
        ))
        if not df.empty:
            df["stat_date"] = pd.to_datetime(df["stat_date"])
        # 补全缺失日期(防止绘图断档)
        full_idx = pd.date_range(s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"), freq="D")
        if df.empty:
            df = pd.DataFrame({"stat_date": full_idx})
        else:
            df = df.set_index("stat_date").reindex(full_idx).reset_index()
            df = df.rename(columns={"index": "stat_date"})
        # 数值列填0
        for c in ("output_wafers", "move_count", "completed_lots", "scrap_count"):
            if c in df.columns:
                df[c] = df[c].fillna(0).astype(int)
        for c in ("avg_oee", "avg_cycle_time_h"):
            if c in df.columns:
                df[c] = df[c].fillna(0.0).astype(float)
        df["product_type"] = df["product_type"].fillna(product_type)
        return df

    @try_except(default_return=pd.DataFrame())
    def recent(self, days: int = 30, product_type: str = "ALL") -> pd.DataFrame:
        """快捷查询最近N天数据。"""
        end = dt.date.today()
        start = end - dt.timedelta(days=days - 1)
        return self.between(start, end, product_type)


# =============================================================================
# Agent 日志 DAO (编排器使用)
# =============================================================================

class AgentLogDAO:
    """agent_logs 表读写。"""

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or get_db()

    @try_except(default_return=False)
    def insert(self, run_id: str, agent_type: str,
               stage: Optional[str] = None,
               status: str = "success",
               input_snapshot: Any = None,
               output_result: Any = None,
               duration_ms: int = 0,
               error_message: Optional[str] = None) -> bool:
        def js(x: Any) -> Optional[str]:
            if x is None:
                return None
            if isinstance(x, str):
                return x
            try:
                return json.dumps(x, ensure_ascii=False, default=str)
            except Exception:
                return str(x)
        return self.db.insert_many(TABLE_AGENT_LOGS, [{
            "run_id": run_id,
            "agent_type": agent_type,
            "stage": stage,
            "status": status,
            "input_snapshot": js(input_snapshot),
            "output_result": js(output_result),
            "duration_ms": int(duration_ms or 0),
            "error_message": error_message,
        }]) == 1

    @try_except(default_return=pd.DataFrame())
    def list_by_run(self, run_id: str) -> pd.DataFrame:
        return self.db.query_df(
            f"SELECT * FROM {TABLE_AGENT_LOGS} WHERE run_id=? ORDER BY id ASC",
            (run_id,),
        )

    @try_except(default_return=pd.DataFrame())
    def recent_runs(self, limit: int = 20) -> pd.DataFrame:
        """获取最近N次全链路run的日志概要。"""
        sql = f"""
            SELECT run_id, created_at,
                   COUNT(CASE WHEN status='success' THEN 1 END) AS succ_steps,
                   COUNT(CASE WHEN status<>'success' THEN 1 END) AS fail_steps,
                   SUM(duration_ms) AS total_ms
            FROM {TABLE_AGENT_LOGS}
            GROUP BY run_id
            ORDER BY MAX(id) DESC
            LIMIT ?
        """
        return self.db.query_df(sql, (limit,))

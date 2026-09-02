"""
FabCapacityAgent - 产能计算核心引擎 (CapacityCalculator)

职责: 基于 lot_history / equipment_events / lots 三张表, 计算
      全厂 & 工序维度的所有 KPI, 供 Services 和 Agent 调用。

核心指标:
  OEE 三要素     - Availability(可用率), Performance(性能率), Quality(良率)
  OEE = A × P × Q
  产能类        - 理论产能 / 有效产能 / UPH(每小时产出) / Throughput(吞吐量)
  时间类        - CycleTime(批次周期) / WaitTime(等待) / Move(步数)
  库存类        - WIP(在制) 按工序分布
  瓶颈类        - Utilization(设备利用率) / BottleneckRate(瓶颈率)

所有方法:
  1) 有 @try_except 兜底, 失败时返回空DF/零值, 不抛异常中断上游
  2) 参数均有类型注解 + 默认值
  3) 返回值: 结构化 DataFrame 或 业务模型对象 CapacitySnapshot
"""

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict

import numpy as np
import pandas as pd

from models.database import DatabaseManager, get_db
from models.wafer import LotsDAO
from models.equipment import EquipmentDAO
from models.capacity import (
    CapacitySnapshot,
    ProcessKPI,
)

from utils.helpers import (
    get_logger,
    try_except,
    parse_datetime,
    hours_between,
    safe_div,
    safe_round,
    get_config,
)
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    EQUIP_STATUS_RUN,
    EQUIP_STATUS_IDLE,
    EQUIP_STATUS_DOWN,
    EQUIP_STATUS_PM,
    EQUIP_STATUS_SETUP,
    TABLE_LOT_HISTORY,
    TABLE_EQUIPMENT_EVENTS,
    TABLE_LOTS,
    TABLE_EQUIPMENT,
    EVENT_EQUIP_DOWN,
    EVENT_PM_START,
    EVENT_SETUP_START,
)

logger = get_logger("CapacityCalculator", level="INFO")


# =============================================================================
# 主类: CapacityCalculator
# =============================================================================

class CapacityCalculator:
    """
    产能计算核心引擎。

    典型用法:
        calc = CapacityCalculator()
        snap = calc.build_snapshot()        # 全厂快照
        print(snap.overall_oee, snap.bottleneck_rank)

        # 按指定时间窗口重算
        end = dt.datetime.now()
        start = end - dt.timedelta(hours=24)
        df_oee = calc.oee_by_process(start, end)
    """

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or get_db()
        self.lots_dao = LotsDAO(self.db)
        self.equip_dao = EquipmentDAO(self.db)

        # 读取工序标准时间 (settings.yaml -> production.processes.*.process_time)
        self.std_process_times: Dict[str, float] = {
            p: float(get_config("production", "processes", default={})
                     .get(p, {}).get("process_time", 2.0))
            for p in ALL_PROCESSES
        }
        # 每批晶圆片数
        self.wafers_per_lot: int = int(get_config("production", "wafers_per_lot", default=25))
        # 每周运行小时数
        self.hours_per_week: int = int(get_config("production", "operating_hours", default=168))

    # =========================================================================
    # 公共便捷入口: 构建结构化快照
    # =========================================================================

    @try_except(default_return=CapacitySnapshot())
    def build_snapshot(
        self,
        window_hours: int = 24,
        history_days_for_ct: int = 14,
        bottleneck_threshold: float = 0.85,
    ) -> CapacitySnapshot:
        """
        一次性计算全量KPI, 返回 CapacitySnapshot (给 PerceptionAgent 用)。

        Args:
            window_hours: 近 N 小时产出窗口, 用于 UPH / Throughput / Move
            history_days_for_ct: 近 N 天用于平均 CycleTime 统计
            bottleneck_threshold: 利用率 > 此阈值标记为瓶颈工序

        Returns:
            CapacitySnapshot 结构化对象
        """
        now_t = dt.datetime.now()
        snap = CapacitySnapshot(snapshot_time=now_t)

        # (A) 按工序维度计算KPI
        window_start = now_t - dt.timedelta(hours=window_hours)
        df_kpi = self.oee_by_process(window_start, now_t)
        if df_kpi.empty:
            df_kpi = pd.DataFrame(
                columns=[
                    "process", "equipment_count", "utilization",
                    "availability", "performance", "quality", "oee",
                    "uph", "avg_cycle_time_h",
                ]
            )

        # 合并 WIP / 理论产能
        wip_df = self.wip_distribution()
        theoretic_df = self.theoretical_capacity_by_process()

        # 合并为 by_process dict
        for p in ALL_PROCESSES:
            row = df_kpi[df_kpi["process"] == p]
            pkpi = ProcessKPI(process=p)
            pkpi.equipment_count = int(self.equipment_count(p))

            if not row.empty:
                r = row.iloc[0]
                pkpi.availability = safe_round(float(r.get("availability", 0)), 4)
                pkpi.performance = safe_round(float(r.get("performance", 0)), 4)
                pkpi.quality = safe_round(float(r.get("quality", 0)), 4)
                pkpi.oee = safe_round(pkpi.availability * pkpi.performance * pkpi.quality, 4)
                pkpi.utilization = safe_round(float(r.get("utilization", 0)), 4)
                pkpi.uph = safe_round(float(r.get("uph", 0)), 2)
                pkpi.avg_cycle_time_h = safe_round(float(r.get("avg_cycle_time_h", 0)), 2)
            # WIP
            w = wip_df[wip_df["process"] == p]
            if not w.empty:
                pkpi.wip_wafers = int(w.iloc[0].get("wafers", 0))
            # 瓶颈判定
            th_row = theoretic_df[theoretic_df["process"] == p]
            if not th_row.empty and pkpi.uph > 0:
                effective = float(th_row.iloc[0].get("effective_uph", 0))
                pkpi.bottleneck_rate = safe_div(pkpi.uph, effective, default=0.0)
            pkpi.is_bottleneck = pkpi.utilization >= bottleneck_threshold

            snap.by_process[p] = pkpi

        # 瓶颈排序 (按 utilization 降序)
        rank = sorted(
            [p for p in ALL_PROCESSES if snap.by_process[p].is_bottleneck],
            key=lambda p: snap.by_process[p].utilization,
            reverse=True,
        )
        if not rank:
            # 没有明显瓶颈, 取利用率前3
            rank = sorted(
                ALL_PROCESSES,
                key=lambda p: snap.by_process[p].utilization,
                reverse=True,
            )[:3]
        snap.bottleneck_rank = rank

        # (B) 全厂级聚合
        # 全厂 OEE: 按设备数加权平均 (非简单平均)
        if df_kpi.empty:
            weights = np.array([self.equipment_count(p) for p in ALL_PROCESSES])
            oeelist = [snap.by_process[p].oee for p in ALL_PROCESSES]
            avail = [snap.by_process[p].availability for p in ALL_PROCESSES]
            perf = [snap.by_process[p].performance for p in ALL_PROCESSES]
            qual = [snap.by_process[p].quality for p in ALL_PROCESSES]
            wsum = weights.sum() or 1
            snap.overall_oee = safe_round(float(np.average(oeelist, weights=weights)), 4)
            snap.overall_availability = safe_round(float(np.average(avail, weights=weights)), 4)
            snap.overall_performance = safe_round(float(np.average(perf, weights=weights)), 4)
            snap.overall_quality = safe_round(float(np.average(qual, weights=weights)), 4)
        else:
            weights = df_kpi["equipment_count"].replace(0, np.nan).fillna(1).values
            wsum = weights.sum() or 1
            snap.overall_availability = safe_round(
                float(np.average(df_kpi["availability"].values, weights=weights)), 4
            )
            snap.overall_performance = safe_round(
                float(np.average(df_kpi["performance"].values, weights=weights)), 4
            )
            snap.overall_quality = safe_round(
                float(np.average(df_kpi["quality"].values, weights=weights)), 4
            )
            snap.overall_oee = safe_round(
                snap.overall_availability * snap.overall_performance * snap.overall_quality, 4
            )

        # 全厂 UPH = 工序UPH之和
        snap.total_uph = safe_round(sum(snap.by_process[p].uph for p in ALL_PROCESSES), 2)
        # WIP 总量
        snap.wip_total_lots = int(self.lots_dao.count_wip())
        snap.wip_total_wafers = int(self.lots_dao.wip_wafers())

        # 24h 产出 / 完成批数 / Move
        out24 = self.output_in_window(now_t - dt.timedelta(hours=24), now_t)
        snap.daily_output_24h = int(out24.get("output_wafers", 0))
        snap.completed_lots_24h = int(out24.get("completed_lots", 0))
        snap.total_move_24h = int(out24.get("move_count", 0))

        # 平均 CycleTime (近 N 天)
        snap.avg_cycle_time_h = safe_round(
            self.avg_cycle_time(now_t - dt.timedelta(days=history_days_for_ct), now_t), 2
        )

        logger.info(
            f"Snapshot构建完成: OEE={snap.overall_oee:.2%}, "
            f"24h产出={snap.daily_output_24h}片, WIP={snap.wip_total_wafers}片, "
            f"瓶颈Top3={'→'.join(snap.bottleneck_rank[:3])}"
        )
        return snap

    # =========================================================================
    # OEE × 工序 (核心计算)
    # =========================================================================

    @try_except(default_return=pd.DataFrame())
    def oee_by_process(self, start_time: Any, end_time: Any) -> pd.DataFrame:
        """
        计算指定时间窗口内, 每道工序的 OEE 三要素及其衍生指标。

        列: process, equipment_count, availability, performance, quality, oee,
            utilization, uph, avg_cycle_time_h, run_hours, down_hours, idle_hours

        计算逻辑 (按 SEMI 标准 OEE 定义):
        (1) 计划生产总时长 PPT = Σ 每台设备窗口内总时长 - PM时长
        (2) 实际运行时长 RUN = Σ lot_history 中 process_time_h (按工序分组求和)
        (3) 故障/换型停机 DOWN = equipment_events 中 EQUIP_DOWN + SETUP 的 duration
        (4) 可用率 Availability = (PPT - DOWN) / PPT
        (5) 性能率 Performance = (实际产出总标准时长) / RUN
            - 实际产出总标准时长 = Σ (完工批数 × 工序标准时间)
            - 简化: Σ (output_qty × std_process_time / wafers_per_lot)
        (6) 良率 Quality = Σ output_qty / Σ input_qty
        (7) OEE = A × P × Q
        """
        s = parse_datetime(start_time) or dt.datetime(2000, 1, 1)
        e = parse_datetime(end_time) or dt.datetime.now()
        total_h = max(1e-6, (e - s).total_seconds() / 3600.0)

        # 1) 各工序设备台数 & 计划时长
        equip_counts: Dict[str, int] = {p: self.equipment_count(p) for p in ALL_PROCESSES}
        # PM 时长 (每台设备窗口内)
        pm_hours_by_proc = self._aggregate_event_duration(
            s, e, event_types=[EVENT_PM_START], group_by="process"
        )

        rows = []
        for p in ALL_PROCESSES:
            n_eq = equip_counts.get(p, 0)
            if n_eq <= 0:
                continue
            ppt_h = total_h * n_eq  # 窗口内所有该工序设备的总日历时间
            pm_h = float(pm_hours_by_proc.get(p, 0.0))
            planned_prod_h = max(0.0, ppt_h - pm_h)  # 计划生产时间(减去PM)

            # 2) RUN时长 / 产出量 (从 lot_history 聚合)
            lh_stats = self._lot_history_stats(s, e, process=p)
            run_h = float(lh_stats["process_time_h_sum"])
            input_qty = int(lh_stats["input_qty_sum"])
            output_qty = int(lh_stats["output_qty_sum"])
            lots_done = int(lh_stats["lots_count"])
            avg_step_h = float(lh_stats["avg_step_h"])

            # 3) DOWN 时长 (故障 + 换型)
            down_h = float(
                self._aggregate_event_duration(
                    s, e, event_types=[EVENT_EQUIP_DOWN, EVENT_SETUP_START],
                    process=p,
                ).get(p, 0.0)
            )

            # (4) 可用率 A = (计划生产时间 - 非计划停机) / 计划生产时间
            availability = safe_div(planned_prod_h - down_h, planned_prod_h, default=0.0)
            # clamp
            availability = max(0.0, min(1.0, availability))

            # (5) 性能率 P = (Σoutput_qty / wafers_per_lot × std_time) / run_h
            std_time = self.std_process_times.get(p, 2.0)
            standard_run_h = (output_qty / max(1, self.wafers_per_lot)) * std_time
            performance = safe_div(standard_run_h, run_h, default=0.0)
            if performance < 0.2:
                # 退化情况兜底: run_h 异常偏低, 用工序时间估算
                performance = safe_div(std_time, max(std_time + 1e-6, avg_step_h), default=0.5)
            performance = max(0.0, min(1.05, performance))  # 允许小幅度>1

            # (6) 良率 Q
            quality = safe_div(output_qty, input_qty, default=1.0)
            quality = max(0.0, min(1.0, quality))

            # OEE
            oee = availability * performance * quality

            # Utilization: RUN / 总日历时间
            utilization = safe_div(run_h, max(1e-6, ppt_h), default=0.0)
            utilization = max(0.0, min(1.0, utilization))

            # UPH: 窗口内合格产出 / 窗口小时
            uph = safe_div(output_qty, total_h, default=0.0)

            rows.append({
                "process": p,
                "process_cn": PROCESS_NAME_CN.get(p, p),
                "equipment_count": n_eq,
                "planned_hours": safe_round(planned_prod_h, 2),
                "run_hours": safe_round(run_h, 2),
                "down_hours": safe_round(down_h, 2),
                "pm_hours": safe_round(pm_h, 2),
                "availability": safe_round(availability, 4),
                "performance": safe_round(performance, 4),
                "quality": safe_round(quality, 4),
                "oee": safe_round(oee, 4),
                "utilization": safe_round(utilization, 4),
                "uph": safe_round(uph, 2),
                "completed_lots": lots_done,
                "output_qty": output_qty,
                "avg_cycle_time_h": safe_round(avg_step_h, 2),
            })

        return pd.DataFrame(rows)

    # =========================================================================
    # 理论 vs 有效产能
    # =========================================================================

    @try_except(default_return=pd.DataFrame())
    def theoretical_capacity_by_process(self) -> pd.DataFrame:
        """
        计算每道工序的 理论产能 & 有效产能。

        理论产能(Theoretical) = 设备台数 × (每周运行小时 / 工序标准时间) × 每批片数
                               = 满速、无停机、良率100% 的理想每周产出

        有效产能(Effective)    = 理论 × OEE基准
                               = 扣除PM/故障/性能损失/良率后的实际每周能出多少

        返回 DataFrame 列: process, equipment_count, theoretic_wafers_per_week,
                           effective_wafers_per_week, theoretic_uph, effective_uph
        """
        oee_bench = (
            float(get_config("data_generator", "oee_benchmark", default={}).get("availability", 0.9))
            * float(get_config("data_generator", "oee_benchmark", default={}).get("performance", 0.85))
            * float(get_config("data_generator", "oee_benchmark", default={}).get("quality", 0.95))
        )
        rows = []
        for p in ALL_PROCESSES:
            n = self.equipment_count(p)
            std_t = self.std_process_times.get(p, 2.0)
            lots_per_week_per_eq = self.hours_per_week / max(std_t, 1e-6)
            theoretic_wafers = n * lots_per_week_per_eq * self.wafers_per_lot
            effective_wafers = theoretic_wafers * oee_bench
            rows.append({
                "process": p,
                "process_cn": PROCESS_NAME_CN.get(p, p),
                "equipment_count": n,
                "std_process_time_h": std_t,
                "theoretic_wafers_per_week": safe_round(theoretic_wafers, 0),
                "effective_wafers_per_week": safe_round(effective_wafers, 0),
                "theoretic_uph": safe_round(theoretic_wafers / self.hours_per_week, 2),
                "effective_uph": safe_round(effective_wafers / self.hours_per_week, 2),
                "benchmark_oee": safe_round(oee_bench, 4),
            })
        return pd.DataFrame(rows)

    # =========================================================================
    # WIP 分布 / CycleTime / 窗口产出
    # =========================================================================

    @try_except(default_return=pd.DataFrame())
    def wip_distribution(self) -> pd.DataFrame:
        """
        查询当前 WIP 分布, 补齐所有工序(含0值, 便于柱状图渲染)。
        列: process, process_cn, lots, wafers
        """
        df = self.lots_dao.wip_distribution()
        if df.empty:
            df = pd.DataFrame(columns=["process", "lots", "wafers"])
        # 补齐 ALL_PROCESSES
        all_proc = pd.DataFrame({"process": ALL_PROCESSES})
        df = all_proc.merge(df, on="process", how="left").fillna(0)
        df["lots"] = df["lots"].astype(int)
        df["wafers"] = df["wafers"].astype(int)
        df["process_cn"] = df["process"].map(PROCESS_NAME_CN).fillna(df["process"])
        # 加上 NOT_STARTED
        return df

    @try_except(default_return=pd.DataFrame())
    def wip_by_product(self) -> pd.DataFrame:
        """WIP 按产品类型分布。"""
        sql = f"""
            SELECT product_type,
                   COUNT(*) AS lots,
                   SUM(wafers_count) AS wafers
            FROM {TABLE_LOTS}
            WHERE status = 'WIP'
            GROUP BY product_type
            ORDER BY wafers DESC
        """
        df = self.db.query_df(sql)
        df = df if not df.empty else pd.DataFrame(columns=["product_type", "lots", "wafers"])
        return df

    @try_except(default_return=0.0)
    def avg_cycle_time(self, start_time: Any, end_time: Any) -> float:
        """
        计算指定时间区间内完工批次的平均 CycleTime。
        CycleTime = 批次 end_time - start_time (单位小时)
        """
        s = parse_datetime(start_time)
        e = parse_datetime(end_time)
        if s is None or e is None:
            return 0.0
        df = self.lots_dao.completed_lots_between(s, e)
        if df.empty:
            return 0.0
        total_h = 0.0
        cnt = 0
        for _, r in df.iterrows():
            h = hours_between(r["start_time"], r["end_time"])
            if pd.isna(h) or h <= 0:
                continue
            total_h += h
            cnt += 1
        return safe_div(total_h, cnt, default=0.0)

    @try_except(default_return=pd.DataFrame())
    def cycle_time_series(self, days: int = 30) -> pd.DataFrame:
        """
        返回近 N 天的 daily 平均 CycleTime 序列。
        列: stat_date, avg_cycle_time_h, completed_lots
        """
        end = dt.date.today()
        start = end - dt.timedelta(days=days - 1)
        # 利用 completed_lots_between 拉全部, 按 end_time 日期分组
        lots_df = self.lots_dao.completed_lots_between(
            dt.datetime(start.year, start.month, start.day),
            dt.datetime(end.year, end.month, end.day, 23, 59, 59),
        )
        if lots_df.empty:
            return pd.DataFrame(columns=["stat_date", "avg_cycle_time_h", "completed_lots"])
        # 构造日期列
        lots_df["stat_date"] = pd.to_datetime(lots_df["end_time"]).dt.date
        lots_df["ct_h"] = lots_df.apply(
            lambda r: hours_between(r["start_time"], r["end_time"]), axis=1
        )
        grp = lots_df.groupby("stat_date").agg(
            avg_cycle_time_h=("ct_h", "mean"),
            completed_lots=("lot_id", "count"),
        ).reset_index()
        grp["avg_cycle_time_h"] = grp["avg_cycle_time_h"].round(2)
        # 补全缺日期
        full = pd.DataFrame({"stat_date": pd.date_range(str(start), str(end)).date})
        grp = full.merge(grp, on="stat_date", how="left")
        grp[["avg_cycle_time_h", "completed_lots"]] = grp[
            ["avg_cycle_time_h", "completed_lots"]
        ].fillna(0)
        return grp

    @try_except(default_return={})
    def output_in_window(self, start_time: Any, end_time: Any) -> Dict[str, int]:
        """
        汇总指定窗口内的产出指标字典:
          output_wafers, completed_lots, move_count, scrap_count
        """
        s = parse_datetime(start_time)
        e = parse_datetime(end_time)
        if s is None or e is None:
            return {"output_wafers": 0, "completed_lots": 0, "move_count": 0, "scrap_count": 0}

        lots_df = self.lots_dao.completed_lots_between(s, e)
        output = int(lots_df["wafers_count"].sum()) if not lots_df.empty else 0
        lots_cnt = int(len(lots_df))

        steps_df = self.lots_dao.list_steps_between(s, e)
        move_cnt = int(len(steps_df))
        scrap = int(steps_df["scrap_qty"].sum()) if not steps_df.empty else 0

        return {
            "output_wafers": output,
            "completed_lots": lots_cnt,
            "move_count": move_cnt,
            "scrap_count": scrap,
        }

    # =========================================================================
    # 停机时间帕累托 & 设备明细 (DownTime Pareto)
    # =========================================================================

    @try_except(default_return=pd.DataFrame())
    def downtime_pareto(self, start_time: Any, end_time: Any, top_n: int = 10) -> pd.DataFrame:
        """
        停机原因帕累托(按工序×原因聚合停机时长, TopN)。
        列: process, reason, duration_h, lots_affected
        """
        s = parse_datetime(start_time)
        e = parse_datetime(end_time)
        if s is None or e is None:
            return pd.DataFrame()

        df = self.equip_dao.downtime_events(s, e)
        if df.empty:
            return pd.DataFrame(columns=["process", "reason", "duration_h", "lots_affected"])
        # 只取 START 事件 (含 duration_h)
        start_types = [EVENT_EQUIP_DOWN, EVENT_PM_START, EVENT_SETUP_START]
        df = df[df["event_type"].isin(start_types)]

        reason_map = {
            EVENT_EQUIP_DOWN: "故障停机",
            EVENT_PM_START: "预防性维护",
            EVENT_SETUP_START: "换型调试",
        }
        default_reason = df["reason"].fillna("")
        default_reason = default_reason.where(default_reason != "", "其他")
        df["reason_cat"] = df["event_type"].map(reason_map).fillna(default_reason)

        grp = df.groupby(["process", "reason_cat"]).agg(
            duration_h=("duration_h", "sum"),
            lots_affected=("equip_id", "count"),
        ).reset_index()
        grp = grp.rename(columns={"reason_cat": "reason"})
        grp["duration_h"] = grp["duration_h"].round(2)
        grp = grp.sort_values("duration_h", ascending=False).head(top_n).reset_index(drop=True)
        return grp

    # =========================================================================
    # 内部辅助
    # =========================================================================

    def equipment_count(self, process: str) -> int:
        """按工序查设备台数 (带缓存语义, 简单SQL COUNT)。"""
        row = self.db.query_one(
            f"SELECT COUNT(*) AS c FROM {TABLE_EQUIPMENT} WHERE process=?",
            (process,),
        )
        return int(row["c"]) if row else 0

    def _aggregate_event_duration(
        self,
        s: dt.datetime,
        e: dt.datetime,
        event_types: List[str],
        group_by: str = "process",
        process: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        从 equipment_events 拉取事件 duration_h, 按 process/equip_id 分组求和。
        返回 {group_key: sum_duration}
        """
        ph_list = ",".join("?" for _ in event_types)
        where = f"ee.event_type IN ({ph_list}) AND ee.event_time >= ? AND ee.event_time < ?"
        params: List[Any] = list(event_types) + [s.strftime("%Y-%m-%d %H:%M:%S"),
                                                   e.strftime("%Y-%m-%d %H:%M:%S")]
        if process:
            where += " AND eq.process = ?"
            params.append(process)
        sql = f"""
            SELECT eq.{group_by} AS key_, COALESCE(SUM(ee.duration_h),0) AS dur
            FROM {TABLE_EQUIPMENT_EVENTS} ee
            JOIN {TABLE_EQUIPMENT} eq ON eq.equip_id = ee.equip_id
            WHERE {where}
            GROUP BY eq.{group_by}
        """
        try:
            rows = self.db.query(sql, params)
            return {r["key_"]: float(r["dur"] or 0.0) for r in rows}
        except Exception:
            return {}

    def _lot_history_stats(self, s: dt.datetime, e: dt.datetime, process: str) -> Dict[str, float]:
        """
        聚合某工序在窗口内的 lot_history 统计。
        返回 process_time_h_sum, input_qty_sum, output_qty_sum, lots_count, avg_step_h
        """
        sql = f"""
            SELECT
                COALESCE(SUM(process_time_h),0)   AS process_time_h_sum,
                COALESCE(SUM(wait_time_h),0)      AS wait_time_h_sum,
                COALESCE(SUM(input_qty),0)        AS input_qty_sum,
                COALESCE(SUM(output_qty),0)       AS output_qty_sum,
                COUNT(DISTINCT lot_id)            AS lots_count,
                COUNT(*)                          AS steps_count,
                COALESCE(AVG(process_time_h),0)   AS avg_step_h
            FROM {TABLE_LOT_HISTORY}
            WHERE process = ?
              AND start_time >= ?
              AND start_time < ?
        """
        row = self.db.query_one(
            sql,
            (
                process,
                s.strftime("%Y-%m-%d %H:%M:%S"),
                e.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        if row is None:
            return {
                "process_time_h_sum": 0.0, "wait_time_h_sum": 0.0,
                "input_qty_sum": 0.0, "output_qty_sum": 0.0,
                "lots_count": 0.0, "steps_count": 0.0, "avg_step_h": 0.0,
            }
        return {
            "process_time_h_sum": float(row["process_time_h_sum"] or 0),
            "wait_time_h_sum": float(row["wait_time_h_sum"] or 0),
            "input_qty_sum": float(row["input_qty_sum"] or 0),
            "output_qty_sum": float(row["output_qty_sum"] or 0),
            "lots_count": float(row["lots_count"] or 0),
            "steps_count": float(row["steps_count"] or 0),
            "avg_step_h": float(row["avg_step_h"] or 0),
        }


# =============================================================================
# 便捷单例
# =============================================================================

_calculator_instance: Optional[CapacityCalculator] = None


def get_calculator() -> CapacityCalculator:
    """全局单例 CapacityCalculator。"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = CapacityCalculator()
    return _calculator_instance


# =============================================================================
# 模块自检
# =============================================================================

if __name__ == "__main__":
    calc = get_calculator()
    print("=== 近24h 各工序 OEE ===")
    end = dt.datetime.now()
    start = end - dt.timedelta(hours=24)
    df = calc.oee_by_process(start, end)
    if df.empty:
        print("(空)")
    else:
        print(df[["process", "equipment_count", "availability", "performance",
                  "quality", "oee", "utilization", "uph"]].to_string(index=False))
    print()
    print("=== 当前 WIP 分布 ===")
    print(calc.wip_distribution().to_string(index=False))
    print()
    print("=== 理论 / 有效产能 (每周) ===")
    print(calc.theoretical_capacity_by_process().to_string(index=False))
    print()
    print("=== 构建快照 (结构化) ===")
    snap = calc.build_snapshot()
    print(snap.pretty_summary())

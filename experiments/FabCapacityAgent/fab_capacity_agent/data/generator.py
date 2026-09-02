"""
FabCapacityAgent - MES模拟数据生成器

生成 90 天历史数据,目标:
  - 120 台设备 (按 8 道工序分配)
  - 5~8 万条 lot_history (每批 8 步工序)
  - 每台设备的 PM / 故障 / 换型 事件
  - daily_output 日产出汇总 (按工序聚合)
  - 当前在制 WIP 批次 (status='WIP')

数据生成策略:
  1. 设备主数据 -> 静态生成
  2. 工艺路线 -> 从 settings.yaml 读取
  3. 批次流    -> 每天按泊松/均匀分布投料, 顺着工艺路线推进
  4. 工序时间  -> 标准时间 × (1 + 噪声), 周末/夜间降速
  5. 故障      -> 按 MTBF/MTTR 指数分布抽样
  6. PM        -> 每 168h 一次, 持续 8h
  7. 异常事件描述 -> 调用 LLM 智能润色 (LLM 不可用时走本地模板兜底)

入口:
  python data/generator.py            # 默认生成全部
  python data/generator.py --quick    # 快速模式 (7天数据, 调试用)
  python data/generator.py --force    # 强制重建 (DROP + CREATE)
"""

import os
import sys
import math
import random
import argparse
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd

# 让脚本可以直接运行: 把项目根加入 sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models.database import get_db, DatabaseManager
from models.wafer import Lot, LotStep, LotsDAO, make_lot
from models.equipment import Equipment, EquipmentEvent, EquipmentDAO, make_equipment
from models.capacity import DailyOutputRow, DailyOutputDAO

from utils.helpers import (
    get_logger,
    get_config,
    safe_round,
    safe_div,
    try_except,
    generate_id,
)
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    PROCESS_EQUIPMENT_TYPE,
    ALL_PRODUCTS,
    PRODUCT_NAME_CN,
    EQUIP_STATUS_RUN,
    EQUIP_STATUS_IDLE,
    EQUIP_STATUS_DOWN,
    EQUIP_STATUS_PM,
    EQUIP_STATUS_SETUP,
    EVENT_LOT_START,
    EVENT_LOT_COMPLETE,
    EVENT_EQUIP_DOWN,
    EVENT_EQUIP_RECOVER,
    EVENT_PM_START,
    EVENT_PM_END,
    EVENT_SETUP_START,
    EVENT_SETUP_END,
    TABLE_EQUIPMENT,
    TABLE_LOTS,
    TABLE_LOT_HISTORY,
    TABLE_EQUIPMENT_EVENTS,
    TABLE_DAILY_OUTPUT,
)
from utils.llm_client import get_llm, LLMClient, PROVIDER_DEEPSEEK

logger = get_logger("DataGenerator", level="INFO")


# =============================================================================
# 工具函数: 时间/随机
# =============================================================================

def _add_hours(t: dt.datetime, hours: float) -> dt.datetime:
    """安全的小时累加。"""
    return t + dt.timedelta(hours=float(hours))


def _round_to_minute(t: dt.datetime) -> dt.datetime:
    """时间对齐到分钟,降低DB存储精度噪声。"""
    return t.replace(second=0, microsecond=0)


def _is_weekend(t: dt.datetime) -> bool:
    return t.weekday() >= 5


def _is_night(t: dt.datetime) -> bool:
    """夜间 22:00~06:00。"""
    return t.hour >= 22 or t.hour < 6


# =============================================================================
# 主生成器
# =============================================================================

class MESDataGenerator:
    """
    MES 模拟数据生成器主类。

    用法:
        gen = MESDataGenerator(history_days=90, seed=42)
        gen.run(force=True)
    """

    def __init__(
        self,
        history_days: Optional[int] = None,
        lots_per_day: Optional[int] = None,
        seed: Optional[int] = None,
        use_llm_polish: bool = True,
    ) -> None:
        # 读取配置
        self.history_days = history_days or int(
            get_config("data_generator", "history_days", default=90)
        )
        self.lots_per_day = lots_per_day or int(
            get_config("data_generator", "lots_per_day", default=60)
        )
        self.seed = seed if seed is not None else int(
            get_config("data_generator", "seed", default=42)
        )
        # 设备分布 & 工序时间
        self.equip_dist: Dict[str, int] = get_config(
            "equipment", "distribution", default={}
        ) or {}
        self.process_time: Dict[str, float] = {
            p: float(get_config("production", "processes", default={}).get(p, {}).get("process_time", 2.0))
            for p in ALL_PROCESSES
        }
        # 工艺路线
        self.process_routes: Dict[str, List[str]] = get_config(
            "production", "process_routes", default={}
        ) or {}
        # OEE 基准
        self.oee_bench = get_config("data_generator", "oee_benchmark", default={}) or {}
        # 故障参数
        self.fail_params = get_config("data_generator", "failure_params", default={}) or {}
        # PM 比例
        self.pm_ratio = float(get_config("production", "pm_ratio", default=0.05))

        # 设置随机种子 (numpy + python random)
        random.seed(self.seed)
        np.random.seed(self.seed)

        # DAO
        self.db: DatabaseManager = get_db()
        self.lots_dao = LotsDAO(self.db)
        self.equip_dao = EquipmentDAO(self.db)
        self.daily_dao = DailyOutputDAO(self.db)

        # LLM 客户端 (用于润色异常描述, 可关)
        self.llm: Optional[LLMClient] = None
        self.use_llm_polish = use_llm_polish
        if self.use_llm_polish:
            try:
                self.llm = get_llm(provider=PROVIDER_DEEPSEEK)
            except Exception as exc:
                logger.warning(f"LLM 客户端初始化失败, 走本地模板兜底: {exc}")
                self.llm = None

        # 生成过程的中间状态
        self.equipments: Dict[str, Equipment] = {}                 # equip_id -> Equipment
        self.equip_by_process: Dict[str, List[str]] = defaultdict(list)  # process -> [equip_id]
        self.equip_last_free_at: Dict[str, dt.datetime] = {}       # equip_id -> 最近一次空闲时间
        self.equip_next_pm_at: Dict[str, dt.datetime] = {}         # equip_id -> 下次PM时间

        # 统计
        self.stats = {
            "equipment": 0,
            "lots": 0,
            "lot_history": 0,
            "events": 0,
            "daily_output": 0,
        }

    # =========================================================================
    # Step A: 生成设备主数据
    # =========================================================================
    def generate_equipment(self) -> List[Equipment]:
        """生成 120 台设备主数据, 写入 equipment 表。"""
        logger.info(f"生成设备主数据 (共 {sum(self.equip_dist.values())} 台)...")
        equipments: List[Equipment] = []
        install_base = dt.datetime(2022, 1, 1)

        for process, count in self.equip_dist.items():
            equip_type = PROCESS_EQUIPMENT_TYPE.get(process, f"{process}_Tool")
            for i in range(1, count + 1):
                # 编号: EQ-PHOTO-01, EQ-ETCH-01 ...
                equip_id = f"EQ-{process}-{i:02d}"
                # 安装日期: 2022~2024 之间随机
                install_date = install_base + dt.timedelta(
                    days=random.randint(0, 800)
                )
                eq = make_equipment(
                    equip_id=equip_id,
                    equip_type=equip_type,
                    process=process,
                    status=random.choices(
                        [EQUIP_STATUS_IDLE, EQUIP_STATUS_RUN, EQUIP_STATUS_PM],
                        weights=[0.5, 0.4, 0.1],
                    )[0],
                    model=f"{equip_type}-2024",
                    location=f"BAY-{process[0]}{i:02d}",
                )
                eq.install_date = install_date
                eq.total_run_hours = safe_round(random.uniform(5000, 25000), 1)
                equipments.append(eq)

                self.equipments[equip_id] = eq
                self.equip_by_process[process].append(equip_id)

        # 批量写入
        inserted = self.equip_dao.bulk_insert_equipment(equipments)
        self.stats["equipment"] = inserted
        logger.info(f"  ✓ 写入 {inserted} 台设备")
        return equipments

    # =========================================================================
    # Step B: 生成历史 lot 流 + lot_history + 设备事件
    # =========================================================================
    def generate_history(self, end_time: Optional[dt.datetime] = None) -> None:
        """
        生成 history_days 天的历史批次流:
          每天投料 lots_per_day 批, 沿工艺路线推进, 写入 lots/lot_history/equipment_events。

        策略:
          - 用时间轴向前推进, 每天生成 N 个 lot
          - 每个 lot 顺着工艺路线依次加工, 各工序时间带噪声
          - 设备占用通过 equip_last_free_at 简单排队
          - 按概率随机插入故障/PM/换型事件
        """
        if not self.equipments:
            self.generate_equipment()

        end_time = end_time or dt.datetime.now().replace(minute=0, second=0, microsecond=0)
        start_time = end_time - dt.timedelta(days=self.history_days)
        logger.info(
            f"生成历史数据: {start_time.date()} → {end_time.date()} "
            f"({self.history_days}天, 日均{self.lots_per_day}批)"
        )

        # 初始化设备占用时间轴: 全部空闲
        for eid in self.equipments:
            self.equip_last_free_at[eid] = start_time
            # PM 周期起点: 每台设备错开, 避免同时停机
            pm_freq = float(self.fail_params.get("pm_frequency", 168))
            self.equip_next_pm_at[eid] = start_time + dt.timedelta(
                hours=random.uniform(0, pm_freq)
            )

        all_lots: List[Lot] = []
        all_steps: List[LotStep] = []
        all_events: List[EquipmentEvent] = []

        # 按天推进
        current = start_time
        day_index = 0
        lot_seq = 0

        # 用于统计 daily_output (key=date -> 聚合)
        daily_agg: Dict[dt.date, Dict[str, int]] = defaultdict(
            lambda: {"output": 0, "move": 0, "lots": 0, "scrap": 0, "oee_sum": 0.0, "oee_cnt": 0, "ct_sum": 0.0, "ct_cnt": 0}
        )

        while current < end_time:
            day_index += 1
            # 当日投料数 (周末降 20%)
            base_lots = self.lots_per_day
            if _is_weekend(current):
                base_lots = int(base_lots * 0.8)
            # 加点噪声
            n_lots_today = max(1, int(np.random.normal(base_lots, base_lots * 0.1)))

            # 投料时间: 当日 8:00~20:00 之间均匀分布
            for _ in range(n_lots_today):
                lot_seq += 1
                # 产品类型按权重分配
                product = random.choices(ALL_PRODUCTS, weights=[0.4, 0.35, 0.25])[0]
                # 投料时间
                release_hour = random.uniform(8, 20)
                release_t = current.replace(hour=0, minute=0) + dt.timedelta(hours=release_hour)
                release_t = _round_to_minute(release_t)

                lot = make_lot(
                    product_type=product,
                    wafers_count=25,
                    start_time=release_t,
                    seq=lot_seq,
                )
                lot.priority = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]

                # 沿工艺路线推进 (传入 cutoff=end_time, 超过则停在当前工序, WIP 分布更真实)
                route = self.process_routes.get(product, ALL_PROCESSES)
                steps, events, completed, end_t, yield_rate, cutoff_hit = self._simulate_lot_route(
                    lot=lot, route=route, release_t=release_t, cutoff_time=end_time
                )
                all_steps.extend(steps)
                all_events.extend(events)

                # 判断状态: 完整走完路线且未超 cutoff -> 完工; 否则 WIP
                if completed and not cutoff_hit and end_t <= end_time:
                    lot.status = "DONE"
                    lot.end_time = end_t
                    lot.current_step = len(route)
                    lot.current_process = route[-1]
                    lot.yield_rate = yield_rate

                    # 计入 daily_output (按完工日)
                    done_date = end_t.date()
                    daily_agg[done_date]["output"] += int(lot.wafers_count * yield_rate)
                    daily_agg[done_date]["lots"] += 1
                    daily_agg[done_date]["scrap"] += int(lot.wafers_count * (1 - yield_rate))
                    daily_agg[done_date]["ct_sum"] += (end_t - release_t).total_seconds() / 3600
                    daily_agg[done_date]["ct_cnt"] += 1
                else:
                    # 仍在制: current_step/current_process 标记当前推进到哪一步
                    lot.status = "WIP"
                    if steps:
                        last_step = steps[-1]
                        lot.current_step = last_step.step_index
                        lot.current_process = last_step.process

                all_lots.append(lot)

            # 推进到下一天
            current = current + dt.timedelta(days=1)

            # 中途 flush 一次, 避免内存堆积
            if len(all_steps) >= 10000:
                self._flush_history(all_lots, all_steps, all_events)
                all_lots.clear()
                all_steps.clear()
                all_events.clear()

        # 最后一次 flush
        self._flush_history(all_lots, all_steps, all_events)

        # 写 daily_output
        self._write_daily_output(daily_agg, start_time, end_time)
        logger.info(
            f"  ✓ 累计写入: lots={self.stats['lots']}, "
            f"lot_history={self.stats['lot_history']}, events={self.stats['events']}"
        )

    # -------------------------------------------------------------------------
    def _simulate_lot_route(
        self,
        lot: Lot,
        route: List[str],
        release_t: dt.datetime,
        cutoff_time: Optional[dt.datetime] = None,
    ) -> Tuple[List[LotStep], List[EquipmentEvent], bool, dt.datetime, float, bool]:
        """
        模拟一个 lot 沿工艺路线的加工过程。

        Args:
            lot: 批次对象
            route: 工艺路线 (工序代码列表)
            release_t: 投料时间
            cutoff_time: 截止时间, 若某步开始时间超过此值则停止模拟 (lot 标记为 WIP)

        返回: (steps, events, completed, end_time, yield_rate, cutoff_hit)
            cutoff_hit: 是否因超过截止时间而提前停止
        """
        steps: List[LotStep] = []
        events: List[EquipmentEvent] = []

        current_t = release_t
        wafers_in = lot.wafers_count
        total_scraps = 0
        completed = True
        cutoff_hit = False

        for step_idx, process in enumerate(route, start=1):
            # 找可用设备: 选当前最早空闲的同类设备
            cand_equip_ids = self.equip_by_process.get(process, [])
            if not cand_equip_ids:
                # 没设备 (理论上不会发生), 跳过
                completed = False
                break

            # 选最早空闲的设备
            eid = min(cand_equip_ids, key=lambda x: self.equip_last_free_at[x])
            equip_free_at = self.equip_last_free_at[eid]

            # 设备现在被占用, lot 排队等到 equip_free_at
            wait_start = current_t
            wait_until = max(current_t, equip_free_at)

            # 若排队后已超过 cutoff, 停止模拟 (lot 停在当前工序, 成为 WIP)
            if cutoff_time is not None and wait_until >= cutoff_time:
                completed = False
                cutoff_hit = True
                break

            wait_h = (wait_until - wait_start).total_seconds() / 3600.0

            # 检查是否触发 PM (PM 优先于生产)
            pm_freq = float(self.fail_params.get("pm_frequency", 168))
            pm_dur = float(self.fail_params.get("pm_duration", 8))
            if wait_until >= self.equip_next_pm_at[eid]:
                # 插入 PM 事件
                pm_start = wait_until
                pm_end = _add_hours(pm_start, pm_dur)
                events.append(EquipmentEvent(
                    equip_id=eid,
                    event_type=EVENT_PM_START,
                    event_time=pm_start,
                    end_time=pm_end,
                    duration_h=pm_dur,
                    reason="计划性预防维护",
                    detail=f"按周期 {pm_freq}h 触发的 PM, 持续 {pm_dur}h",
                ))
                events.append(EquipmentEvent(
                    equip_id=eid,
                    event_type=EVENT_PM_END,
                    event_time=pm_end,
                    end_time=pm_end,
                    duration_h=0,
                    reason="PM 完成",
                ))
                # 推迟 lot 开始时间
                wait_until = pm_end
                wait_h = (wait_until - wait_start).total_seconds() / 3600.0
                # 安排下次 PM
                self.equip_next_pm_at[eid] = pm_end + dt.timedelta(hours=pm_freq)

            # 故障抽样 (按 MTBF 指数分布)
            mtbf = float(self.fail_params.get("mtbf", 48))
            mttr = float(self.fail_params.get("mttr", 4))
            # 该设备在本次加工期间发生故障的概率 ≈ process_time / mtbf
            std_time = self.process_time.get(process, 2.0)
            fail_prob = min(0.15, std_time / max(mtbf, 1.0))
            if random.random() < fail_prob:
                # 触发故障, 持续 mttr 附近
                down_dur = max(0.5, np.random.exponential(mttr))
                down_start = wait_until
                down_end = _add_hours(down_start, down_dur)
                # 用 LLM 生成故障描述
                reason_text = self._polish_event_reason(
                    event_type=EVENT_EQUIP_DOWN,
                    process=process,
                    equip_id=eid,
                    duration_h=down_dur,
                )
                events.append(EquipmentEvent(
                    equip_id=eid,
                    event_type=EVENT_EQUIP_DOWN,
                    event_time=down_start,
                    end_time=down_end,
                    duration_h=safe_round(down_dur, 2),
                    reason=reason_text,
                    detail=f"{PROCESS_NAME_CN.get(process, process)} 工序设备 {eid} 突发停机",
                ))
                events.append(EquipmentEvent(
                    equip_id=eid,
                    event_type=EVENT_EQUIP_RECOVER,
                    event_time=down_end,
                    end_time=down_end,
                    duration_h=0,
                    reason="设备修复恢复运行",
                ))
                wait_until = down_end
                wait_h = (wait_until - wait_start).total_seconds() / 3600.0

            # 换型事件 (跨产品时 5% 概率)
            if step_idx == 1 and random.random() < 0.05:
                setup_dur = random.uniform(0.5, 1.5)
                setup_start = wait_until
                setup_end = _add_hours(setup_start, setup_dur)
                events.append(EquipmentEvent(
                    equip_id=eid,
                    event_type=EVENT_SETUP_START,
                    event_time=setup_start,
                    end_time=setup_end,
                    duration_h=safe_round(setup_dur, 2),
                    reason=f"切换到 {PRODUCT_NAME_CN.get(lot.product_type, lot.product_type)} 配方",
                ))
                events.append(EquipmentEvent(
                    equip_id=eid,
                    event_type=EVENT_SETUP_END,
                    event_time=setup_end,
                    end_time=setup_end,
                    duration_h=0,
                    reason="换型完成",
                ))
                wait_until = setup_end

            # 计算实际加工时间: 标准时间 × (1 + 噪声)
            # 夜间/周末稍微慢一点
            speed_factor = 1.0
            if _is_night(wait_until):
                speed_factor *= 1.08
            if _is_weekend(wait_until):
                speed_factor *= 1.05
            noise = np.random.normal(0, 0.1)
            process_h = max(0.1, std_time * speed_factor * (1 + noise))

            step_start = wait_until
            step_end = _add_hours(step_start, process_h)
            step_end = _round_to_minute(step_end)

            # 良率: 每步可能产生少量 scrap
            scrap_rate = random.uniform(0.0, 0.01)
            scrap_qty = int(wafers_in * scrap_rate)
            output_qty = wafers_in - scrap_qty
            total_scraps += scrap_qty

            # 产出事件
            events.append(EquipmentEvent(
                equip_id=eid,
                event_type=EVENT_LOT_START,
                event_time=step_start,
                end_time=step_end,
                lot_id=lot.lot_id,
                duration_h=safe_round(process_h, 2),
                reason=f"{lot.lot_id} 在 {PROCESS_NAME_CN.get(process, process)} 开工",
            ))
            events.append(EquipmentEvent(
                equip_id=eid,
                event_type=EVENT_LOT_COMPLETE,
                event_time=step_end,
                end_time=step_end,
                lot_id=lot.lot_id,
                duration_h=0,
                reason=f"{lot.lot_id} 在 {PROCESS_NAME_CN.get(process, process)} 完工",
            ))

            steps.append(LotStep(
                lot_id=lot.lot_id,
                process=process,
                step_index=step_idx,
                equip_id=eid,
                start_time=step_start,
                end_time=step_end,
                input_qty=wafers_in,
                output_qty=output_qty,
                scrap_qty=scrap_qty,
                wait_time_h=safe_round(wait_h, 2),
                process_time_h=safe_round(process_h, 2),
                status="DONE",
            ))

            # 更新设备空闲时间
            self.equip_last_free_at[eid] = step_end
            # 推进 lot 时间
            current_t = step_end
            wafers_in = output_qty

        yield_rate = safe_div(wafers_in, lot.wafers_count, default=1.0)
        return steps, events, completed, current_t, safe_round(yield_rate, 4), cutoff_hit

    # -------------------------------------------------------------------------
    def _flush_history(
        self,
        lots: List[Lot],
        steps: List[LotStep],
        events: List[EquipmentEvent],
    ) -> None:
        """批量 flush 一批 lot/step/event 到 DB。"""
        if lots:
            self.stats["lots"] += self.lots_dao.bulk_insert_lots(lots)
        if steps:
            self.stats["lot_history"] += self.lots_dao.bulk_insert_steps(steps)
        if events:
            self.stats["events"] += self.equip_dao.bulk_insert_events(events)

    # -------------------------------------------------------------------------
    def _write_daily_output(
        self,
        daily_agg: Dict[dt.date, Dict[str, int]],
        start_time: dt.datetime,
        end_time: dt.datetime,
    ) -> None:
        """把 daily_agg 转成 DailyOutputRow 写入 daily_output 表。"""
        rows: List[DailyOutputRow] = []
        # 全日期范围, 缺失日补零
        cur = start_time.date()
        end = end_time.date()
        oee_bench = float(self.oee_bench.get("availability", 0.9)) * \
                    float(self.oee_bench.get("performance", 0.85)) * \
                    float(self.oee_bench.get("quality", 0.95))
        while cur <= end:
            agg = daily_agg.get(cur, {})
            output = int(agg.get("output", 0))
            move = int(agg.get("move", 0)) or output * 8  # 默认按8步估算
            lots = int(agg.get("lots", 0))
            scrap = int(agg.get("scrap", 0))
            ct_avg = safe_div(agg.get("ct_sum", 0), agg.get("ct_cnt", 0), default=0)
            # OEE 加点噪声
            oee_avg = oee_bench * random.uniform(0.9, 1.05)
            rows.append(DailyOutputRow(
                stat_date=cur,
                product_type="ALL",
                output_wafers=output,
                move_count=move,
                completed_lots=lots,
                avg_oee=safe_round(oee_avg, 4),
                avg_cycle_time_h=safe_round(ct_avg, 2),
                scrap_count=scrap,
            ))
            cur += dt.timedelta(days=1)

        inserted = self.daily_dao.upsert_rows(rows)
        self.stats["daily_output"] = inserted
        logger.info(f"  ✓ 写入 daily_output: {inserted} 行")

    # =========================================================================
    # Step C: 用 LLM 润色事件描述
    # =========================================================================
    @try_except(default_return="")
    def _polish_event_reason(
        self,
        event_type: str,
        process: str,
        equip_id: str,
        duration_h: float,
    ) -> str:
        """
        用 LLM 生成更自然的故障/异常事件描述。
        LLM 不可用时走本地模板兜底 (保证生成流程不中断)。

        Args:
            event_type: 事件类型常量
            process: 工序代码
            equip_id: 设备ID
            duration_h: 持续时间(小时)

        Returns:
            中文描述字符串
        """
        # 本地模板兜底 (优先, 因为 LLM 调用慢且配额有限, 大量事件用模板)
        local_templates = {
            EVENT_EQUIP_DOWN: [
                f"{PROCESS_NAME_CN.get(process, process)} 设备 {equip_id} 模块异常告警, 紧急停机检修",
                f"{equip_id} 出现 {PROCESS_NAME_CN.get(process, process)} 工艺参数漂移, 触发安全联锁",
                f"{equip_id} 冷却系统压力异常, 自动停机保护",
                f"{equip_id} 光学/电气部件故障, 工程师介入维修",
                f"{equip_id} 真空度异常, 紧急停机排查",
            ],
            EVENT_PM_START: [
                f"{equip_id} 按计划进入 PM 维护窗口",
                f"{equip_id} 周期性保养启动",
            ],
        }
        template_list = local_templates.get(event_type, [f"{equip_id} 触发 {event_type}"])
        # 90% 走本地模板, 10% 调用 LLM 润色 (避免大量 LLM 调用拖慢生成)
        if random.random() > 0.1 or self.llm is None:
            return random.choice(template_list)

        # 调 LLM 生成更丰富的描述
        prompt = (
            f"你是半导体Fab设备工程师。请用一句不超过30字的中文,"
            f"描述一次 {PROCESS_NAME_CN.get(process, process)} 工序 {equip_id} 设备的 {event_type} 事件,"
            f"持续约 {duration_h:.1f} 小时。要求专业、具体、可读, 只输出描述本身。"
        )
        text = self.llm.chat(prompt, max_tokens=80, temperature=0.7)
        if text and len(text) < 100:
            return text.strip().strip("。.")
        return random.choice(template_list)

    # =========================================================================
    # 入口
    # =========================================================================
    def run(self, force: bool = False) -> Dict[str, int]:
        """
        主入口: 建表 -> 生成设备 -> 生成历史 -> 输出统计。

        Args:
            force: True 则 DROP 重建所有表

        Returns:
            统计字典
        """
        logger.info("=" * 60)
        logger.info("MES 模拟数据生成器启动")
        logger.info(f"  数据库: {self.db.path}")
        logger.info(f"  历史天数: {self.history_days} 天")
        logger.info(f"  日均投料: {self.lots_per_day} 批")
        logger.info(f"  随机种子: {self.seed}")
        logger.info(f"  LLM 润色: {'开启' if (self.use_llm_polish and self.llm) else '关闭(本地模板)'}")
        logger.info("=" * 60)

        # 1) 初始化表结构
        self.db.initialize_schema(force=force)

        # 2) 如果不强制重建, 且已有数据, 跳过生成
        if not force:
            existing = self.db.count(TABLE_LOT_HISTORY)
            if existing > 0:
                logger.info(f"检测到已有 {existing} 条 lot_history, 跳过生成 (使用 --force 强制重建)")
                return self.stats

        # 3) 生成设备
        self.generate_equipment()

        # 4) 生成历史
        self.generate_history()

        logger.info("=" * 60)
        logger.info("✓ 数据生成完成")
        logger.info(f"  equipment       : {self.stats['equipment']}")
        logger.info(f"  lots            : {self.stats['lots']}")
        logger.info(f"  lot_history     : {self.stats['lot_history']}")
        logger.info(f"  equipment_events: {self.stats['events']}")
        logger.info(f"  daily_output    : {self.stats['daily_output']}")
        logger.info("=" * 60)
        return self.stats


# =============================================================================
# CLI 入口
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="FabCapacityAgent MES 模拟数据生成器")
    parser.add_argument("--days", type=int, default=None, help="历史数据天数 (默认90)")
    parser.add_argument("--lots-per-day", type=int, default=None, help="日均投料批数 (默认60)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子 (默认42)")
    parser.add_argument("--force", action="store_true", help="强制 DROP 重建所有表")
    parser.add_argument("--quick", action="store_true", help="快速模式: 7天/15批 (调试用)")
    parser.add_argument("--no-llm", action="store_true", help="禁用 LLM 润色, 全部走本地模板")
    args = parser.parse_args()

    if args.quick:
        args.days = args.days or 7
        args.lots_per_day = args.lots_per_day or 15
        args.force = True
        logger.info("⚡ 快速模式: 7天 / 15批 / 强制重建")

    gen = MESDataGenerator(
        history_days=args.days,
        lots_per_day=args.lots_per_day,
        seed=args.seed,
        use_llm_polish=not args.no_llm,
    )
    gen.run(force=args.force)


if __name__ == "__main__":
    main()

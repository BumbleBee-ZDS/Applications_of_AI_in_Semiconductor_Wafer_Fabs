"""
FabCapacityAgent - 感知 Agent (PerceptionAgent)

职责: 采集 MES 数据 -> 结构化状态快照 (CapacitySnapshot)
      作为整个 Agent 链路的"眼睛", 把 DB 里杂乱的数据变为结构化输入。

PTA 分工:
  perceive: 从 DB 拉取设备/批次/事件/产出, 调用 CapacityCalculator.build_snapshot()
  think:    对快照做基础清洗 (字段裁剪/单位归一/异常初筛)
  act:      返回结构化快照 + 简短文字摘要, 写入 context.snapshot
"""

import os
import sys
import datetime as dt
from typing import Any, Dict, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from agents.base_agent import BaseAgent, AgentContext
from services.capacity_calculator import CapacityCalculator, get_calculator
from models.capacity import CapacitySnapshot
from utils.helpers import get_logger, try_except, safe_round
from utils.constants import (
    AGENT_PERCEPTION,
    PROCESS_NAME_CN,
    ALL_PROCESSES,
)
from utils.llm_client import LLMClient

logger = get_logger("PerceptionAgent", level="INFO")


class PerceptionAgent(BaseAgent):
    """感知 Agent: MES 数据采集 -> CapacitySnapshot。"""

    AGENT_TYPE = AGENT_PERCEPTION
    AGENT_NAME_CN = "感知Agent"

    def __init__(
        self,
        calc: Optional[CapacityCalculator] = None,
        llm: Optional[LLMClient] = None,
        use_llm: Optional[bool] = None,
    ) -> None:
        super().__init__(name=AGENT_PERCEPTION, llm=llm, use_llm=use_llm)
        self.calc = calc or get_calculator()

    # =========================================================================
    # perceive: 数据采集
    # =========================================================================
    def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """
        从 DB 采集当前产能状态, 调用 CapacityCalculator 构建结构化快照。
        """
        window_hours = int(context.extra.get("window_hours", 24))
        self.logger.info(f"采集近 {window_hours}h 数据, 构建产能快照...")

        snapshot = self.calc.build_snapshot(window_hours=window_hours)

        # 同时拉一份 WIP 分布 & 设备状态汇总, 给 think 用
        wip_df = self.calc.wip_distribution()
        equip_status_df = self.calc.equip_dao.status_summary()

        return {
            "snapshot": snapshot.to_dict(),
            "wip_distribution": wip_df.to_dict(orient="records"),
            "equipment_status": equip_status_df.to_dict(orient="records"),
            "window_hours": window_hours,
            "collected_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # =========================================================================
    # think: 数据清洗 + 异常初筛
    # =========================================================================
    def think(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于感知结果做轻量推理:
          - 识别 OEE 偏低工序 (< 80%)
          - 识别 WIP 异常积压 (> 平均值 1.5 倍)
          - 识别设备故障高发 (DOWN 状态设备 > 10%)
        """
        snap = perception.get("snapshot", {})
        wip_list = perception.get("wip_distribution", [])
        equip_status = perception.get("equipment_status", [])

        # 异常初筛
        low_oee_procs = []
        for p, kpi in (snap.get("by_process") or {}).items():
            oee = float(kpi.get("oee", 0))
            if oee < 0.80:
                low_oee_procs.append({"process": p, "oee": safe_round(oee, 4)})

        # WIP 异常
        wip_values = [w.get("wafers", 0) for w in wip_list if w.get("wafers", 0) > 0]
        avg_wip = sum(wip_values) / max(1, len(wip_values))
        wip_outliers = [
            {"process": w.get("process"), "wafers": w.get("wafers", 0)}
            for w in wip_list
            if w.get("wafers", 0) > avg_wip * 1.5
        ]

        # 设备故障高发
        total_eq = sum(int(e.get("cnt", 0)) for e in equip_status)
        down_cnt = sum(
            int(e.get("cnt", 0))
            for e in equip_status
            if e.get("status") == "DOWN"
        )
        down_ratio = down_cnt / max(1, total_eq)

        return {
            "snapshot": snap,
            "anomalies": {
                "low_oee_processes": low_oee_procs,
                "wip_outliers": wip_outliers,
                "equipment_down_ratio": safe_round(down_ratio, 4),
                "equipment_down_count": down_cnt,
            },
            "summary_text": (
                f"全厂OEE={snap.get('overall_oee', 0)*100:.2f}%, "
                f"WIP={snap.get('wip_total_wafers', 0)}片, "
                f"瓶颈Top3: {'→'.join(snap.get('bottleneck_rank', [])[:3])}"
            ),
        }

    # =========================================================================
    # act: 写入 context + 返回结构化结果
    # =========================================================================
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        把结构化感知结果写入 context.snapshot, 供下游 AnalysisAgent 消费。
        """
        # 构造 CapacitySnapshot 对象回写到 context (在 run() 内通过闭包传递)
        # 注意: 这里通过 self._current_context 间接写
        snap_dict = decision.get("snapshot", {})
        result = {
            "agent": self.AGENT_NAME_CN,
            "snapshot": snap_dict,
            "anomalies": decision.get("anomalies", {}),
            "summary_text": decision.get("summary_text", ""),
            "status": "ok",
        }
        return result

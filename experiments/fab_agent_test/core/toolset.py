"""
core/toolset.py
=================
Agent 可调用的工具集合（Mock 实现）。

包含 4 个工具：
1. get_lot_info(lot_id)              - 查询批次信息（稳定）
2. get_equipment_log(chamber_id)     - 查询机台运行日志（30% 超时，重试 1 次）
3. get_recipe_params(lot_id)         - 查询工艺配方（稳定）
4. get_lot_history(lot_id)           - 批次历史推断（降级用）
"""

import random
import time
from typing import Any, Callable, Dict, Optional

from .evaluator import Evaluator
from data.mock_data import LOT_DB, RECIPE_DB, EQUIP_TIMEOUT_RATE


LogFn = Callable[[str], None]


class ToolSet:
    """Agent 可调用的工具集合"""

    def __init__(self, evaluator: Evaluator, log_fn: LogFn):
        self.evaluator = evaluator
        self.log = log_fn

    # -----------------------------------------------------------------
    # 内部：不稳定的 Equipment API（30% 超时）
    # -----------------------------------------------------------------
    def _call_equipment_api(self, chamber_id: str) -> Optional[Dict[str, Any]]:
        """模拟不稳定的 Equipment API：30% 概率返回 None（超时）"""
        if random.random() < EQUIP_TIMEOUT_RATE:
            return None
        return {
            "chamber_id": chamber_id,
            # 实测压力偏高，与配方设定值形成冲突，用于触发 Reflector
            "pressure_mtorr": round(random.uniform(6.8, 7.6), 2),
            "rf_power_w": 1250,
            "temperature_c": 80.0,
            "timestamp": "2026-08-09 14:30:00",
            "status": "ABNORMAL_PRESSURE",
        }

    # -----------------------------------------------------------------
    # 工具 1：查询批次信息
    # -----------------------------------------------------------------
    def get_lot_info(self, lot_id: str) -> Optional[Dict[str, Any]]:
        self.evaluator.record_tool_call("get_lot_info", {"lot_id": lot_id})
        self.log(f"[Tool] 调用 get_lot_info(lot_id={lot_id}) ...")
        info = LOT_DB.get(lot_id)
        if info is None:
            self.log(f"[Tool] ⚠ 未找到批次 {lot_id}")
            return None
        self.log(
            f"[Tool] ✓ 返回批次信息：产品={info['product']}，"
            f"CD目标={info['cd_target_nm']}nm，CD实测={info['cd_measured_nm']}nm，"
            f"状态={info['status']}"
        )
        self.evaluator.add_tokens(str(info))
        return info

    # -----------------------------------------------------------------
    # 工具 2：查询机台运行日志（不稳定，30% 超时，自动重试 1 次）
    # -----------------------------------------------------------------
    def get_equipment_log(self, chamber_id: str) -> Optional[Dict[str, Any]]:
        self.evaluator.record_tool_call("get_equipment_log", {"chamber_id": chamber_id})
        self.log(f"[Tool] 调用设备接口 get_equipment_log(chamber_id={chamber_id}) ...")

        # 第一次尝试
        result = self._call_equipment_api(chamber_id)
        if result is None:
            self.log(f"[Tool] ✗ 设备接口超时（{int(EQUIP_TIMEOUT_RATE*100)}% 概率触发）")
            # 失败自愈策略：重试 1 次
            self.evaluator.retry_count += 1
            self.log("[Tool] ⟳ 重试 1 次 ...")
            time.sleep(0.3)
            result = self._call_equipment_api(chamber_id)
            if result is None:
                self.log("[Tool] ✗ 重试仍失败，需 Planner 调整计划")
                return None
            self.log("[Tool] ✓ 重试成功")
            self.evaluator.timeout_handled = True
        else:
            self.log(
                f"[Tool] ✓ 返回机台日志：压力={result['pressure_mtorr']}mTorr，"
                f"RF功率={result['rf_power_w']}W，状态={result['status']}"
            )
        self.evaluator.add_tokens(str(result))
        return result

    # -----------------------------------------------------------------
    # 工具 3：查询工艺配方
    # -----------------------------------------------------------------
    def get_recipe_params(self, lot_id: str) -> Optional[Dict[str, Any]]:
        self.evaluator.record_tool_call("get_recipe_params", {"lot_id": lot_id})
        self.log(f"[Tool] 调用 get_recipe_params(lot_id={lot_id}) ...")
        recipe = RECIPE_DB.get(lot_id)
        if recipe is None:
            self.log(f"[Tool] ⚠ 未找到批次 {lot_id} 的配方")
            return None
        self.log(
            f"[Tool] ✓ 返回配方：recipe_id={recipe['recipe_id']}，"
            f"设定压力={recipe['pressure_setpoint_mtorr']}mTorr，"
            f"工艺时间={recipe['etch_time_sec']}s"
        )
        self.evaluator.add_tokens(str(recipe))
        return recipe

    # -----------------------------------------------------------------
    # 工具 4（降级）：批次历史推断（设备接口不可用时）
    # -----------------------------------------------------------------
    def get_lot_history(self, lot_id: str) -> Dict[str, Any]:
        self.evaluator.record_tool_call("get_lot_history", {"lot_id": lot_id})
        self.log(f"[Tool] 降级调用 get_lot_history(lot_id={lot_id}) ...")
        info = LOT_DB.get(lot_id, {})
        history = {
            "lot_id": lot_id,
            "history_note": info.get("history", "无历史数据"),
            "inferred_chamber": info.get("chamber_id", "未知"),
        }
        self.log(f"[Tool] ✓ 返回历史推断：{history['history_note']}")
        self.evaluator.add_tokens(str(history))
        return history

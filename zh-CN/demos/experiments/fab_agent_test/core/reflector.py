"""
core/reflector.py
===================
反思器：检查工具返回的数据是否矛盾。

示例冲突：Recipe 显示压力正常(5.0 mTorr)，机台日志实测压力异常(7.x mTorr)
→ 偏差超过 1.0 mTorr → 标记为冲突。
"""

from typing import Any, Callable, Dict

from .evaluator import Evaluator


LogFn = Callable[[str], None]


class Reflector:
    def __init__(self, evaluator: Evaluator, log_fn: LogFn):
        self.evaluator = evaluator
        self.log = log_fn

    def check_conflict(self, tool_results: Dict[str, Any]) -> bool:
        """对比 tool_results 中的 recipe / equipment_log / history，返回是否存在冲突"""
        self.log("[Reflect] 检查数据一致性 ...")
        recipe = tool_results.get("recipe")
        equip = tool_results.get("equipment_log")
        history = tool_results.get("history")

        conflict = False

        if recipe and equip:
            setpoint = float(recipe.get("pressure_setpoint_mtorr") or 0.0)
            actual = float(equip.get("pressure_mtorr") or 0.0)
            if abs(actual - setpoint) > 1.0:
                conflict = True
                self.log(
                    f"[Reflect] ⚡ 发现压力数据矛盾："
                    f"配方设定={setpoint}mTorr，机台实测={actual}mTorr"
                )
            else:
                self.log("[Reflect] 压力数据一致，未发现矛盾")
        elif history and not equip:
            self.log(
                f"[Reflect] 仅历史数据可用（设备日志缺失）：{history.get('history_note', '')}"
            )
        else:
            self.log("[Reflect] 数据不足，无法比对")

        self.evaluator.reflection_valid = conflict
        self.evaluator.add_tokens(f"conflict={conflict}")
        return conflict

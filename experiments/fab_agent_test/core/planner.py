"""
core/planner.py
=================
规划器：接收问题，输出子任务列表 List[str]。

支持失败自愈：当设备接口失败时，调用 adjust_plan_skip_equipment
将"查询机台运行日志"步骤替换为"查询批次历史推断（降级）"，
实现系统韧性中的"失败自愈策略"。
"""

from typing import Callable, List

from .evaluator import Evaluator


LogFn = Callable[[str], None]


class Planner:
    def __init__(self, evaluator: Evaluator, log_fn: LogFn):
        self.evaluator = evaluator
        self.log = log_fn

    def make_plan(self, question: str) -> List[str]:
        """根据问题生成标准 5 步执行计划"""
        self.log("[Planner] 分析问题，生成执行计划 ...")
        plan = [
            "查询批次信息",
            "查询机台运行日志",
            "查询工艺配方",
            "反思检查数据一致性",
            "生成总结报告",
        ]
        self.log(f"[Planner] 计划步骤：{plan}")
        self.evaluator.add_tokens("\n".join(plan))
        return plan

    def adjust_plan_skip_equipment(self, plan: List[str]) -> List[str]:
        """失败自愈策略：跳过设备详情，改用批次历史推断（降级路径）"""
        self.log("[Planner] ⚙ 调整计划：跳过设备详情，改用批次历史推断（降级路径）")
        new_plan: List[str] = []
        for step in plan:
            if "机台" in step or "设备" in step:
                new_plan.append("查询批次历史推断（降级）")
            else:
                new_plan.append(step)
        self.log(f"[Planner] 新计划：{new_plan}")
        self.evaluator.add_tokens("\n".join(new_plan))
        return new_plan

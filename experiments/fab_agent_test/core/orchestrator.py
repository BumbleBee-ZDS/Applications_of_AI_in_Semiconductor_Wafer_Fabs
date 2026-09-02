"""
core/orchestrator.py
======================
编排器（主循环）：依次执行 Planner 生成的步骤，调用 ToolSet，
用 Reflector 检查数据一致性，并生成最终报告。

终止保护：
- max_steps 步数上限（防死循环）
- Evaluator.dead_loop_flag（连续 2 步调用同一工具且参数相同）
"""

import time
from typing import Any, Callable, Dict, List

from .evaluator import Evaluator
from .memory import Memory
from .toolset import ToolSet
from .planner import Planner
from .reflector import Reflector


LogFn = Callable[[str], None]


class Orchestrator:
    def __init__(
        self,
        memory: Memory,
        toolset: ToolSet,
        planner: Planner,
        reflector: Reflector,
        evaluator: Evaluator,
        log_fn: LogFn,
    ):
        self.memory = memory
        self.toolset = toolset
        self.planner = planner
        self.reflector = reflector
        self.evaluator = evaluator
        self.log = log_fn

    # -----------------------------------------------------------------
    # 从问题中提取批次号（纯字符串扫描，不依赖 re）
    # -----------------------------------------------------------------
    @staticmethod
    def _extract_lot_id(question: str) -> str:
        """匹配 W 后跟数字的批次号（如 W12345），未匹配则返回默认 W12345。"""
        for i, ch in enumerate(question):
            if ch == "W" and i + 1 < len(question) and question[i + 1].isdigit():
                j = i + 1
                while j < len(question) and question[j].isdigit():
                    j += 1
                return question[i:j]
        return "W12345"

    # -----------------------------------------------------------------
    # 主运行循环
    # -----------------------------------------------------------------
    def run(self, question: str) -> str:
        self.log("[Orchestrator] 启动分析流程")

        # 1) 提取并记忆批次号
        lot_id = self._extract_lot_id(question)
        self.memory.store("lot_id", lot_id)
        self.log(f"[Memory] 已存储批次号：{lot_id}")

        # 2) Planner 生成计划
        plan = self.planner.make_plan(question)

        tool_results: Dict[str, Any] = {}
        final_report = ""
        plan_adjusted = False
        idx = 0

        # 3) 逐步执行
        while idx < len(plan):
            # 终止条件 1：步数上限
            if self.evaluator.step_count >= self.evaluator.max_steps:
                self.log(
                    f"[Orchestrator] ⛔ 达到最大步数 {self.evaluator.max_steps}，强制终止"
                )
                break
            # 终止条件 2：死循环
            if self.evaluator.dead_loop_flag:
                self.log("[Orchestrator] ⛔ 检测到死循环（连续2步相同调用），强制终止")
                break

            step = plan[idx]
            self.evaluator.step_count += 1
            self.log(f"[Step {self.evaluator.step_count}] ▶ {step}")
            self.evaluator.add_tokens(step)

            lot_id = self.memory.recall("lot_id")

            # —— 步骤分发 ——
            if "批次信息" in step:
                info = self.toolset.get_lot_info(lot_id)
                if info:
                    tool_results["lot_info"] = info

            elif "机台" in step or "设备" in step:
                chamber = tool_results.get("lot_info", {}).get(
                    "chamber_id", "ETCH-CH-007"
                )
                result = self.toolset.get_equipment_log(chamber)
                if result is None:
                    # Planner 自愈：调整计划（仅调整一次，避免反复）
                    if not plan_adjusted:
                        plan = self.planner.adjust_plan_skip_equipment(plan)
                        plan_adjusted = True
                        continue  # 不递增 idx，重跑当前步骤（已被替换为降级步骤）
                    self.log("[Orchestrator] 计划已调整仍失败，跳过该步骤")
                else:
                    tool_results["equipment_log"] = result

            elif "批次历史" in step or "降级" in step:
                history = self.toolset.get_lot_history(lot_id)
                tool_results["history"] = history

            elif "配方" in step or "Recipe" in step:
                recipe = self.toolset.get_recipe_params(lot_id)
                if recipe:
                    tool_results["recipe"] = recipe

            elif "反思" in step:
                self.reflector.check_conflict(tool_results)

            elif "报告" in step or "总结" in step:
                final_report = self._generate_report(question, tool_results)
                self.log("[Orchestrator] 📝 生成最终报告")

            idx += 1
            time.sleep(0.25)  # 视觉延迟，便于观察实时日志

        # 兜底强制生成
        if not final_report:
            final_report = self._generate_report(question, tool_results, forced=True)
            self.log("[Orchestrator] 📝 强制生成兜底报告")

        self.evaluator.final_report = final_report
        self.log("[Orchestrator] ✅ 流程结束")
        return final_report

    # -----------------------------------------------------------------
    # 生成最终报告（模拟 LLM 输出，f-string 拼接）
    # -----------------------------------------------------------------
    def _generate_report(
        self,
        question: str,
        tool_results: Dict[str, Any],
        forced: bool = False,
    ) -> str:
        lot_info = tool_results.get("lot_info", {})
        equip = tool_results.get("equipment_log")
        recipe = tool_results.get("recipe", {})
        history = tool_results.get("history")
        conflict = self.evaluator.reflection_valid
        lot_id = self.memory.recall("lot_id", "未知")

        lines: List[str] = []
        lines.append("# 晶圆缺陷根因分析报告")
        lines.append(f"**问题**：{question}")
        lines.append(f"**批次**：{lot_id}")
        if forced:
            lines.append("> ⚠ 注：流程未正常完成，以下为兜底报告")

        if lot_info:
            lines.append(
                f"**批次信息**：产品={lot_info.get('product')}，"
                f"CD目标={lot_info.get('cd_target_nm')}nm，"
                f"CD实测={lot_info.get('cd_measured_nm')}nm，"
                f"状态={lot_info.get('status')}"
            )
        if equip:
            lines.append(
                f"**机台日志**：腔体={equip.get('chamber_id')}，"
                f"实测压力={equip.get('pressure_mtorr')}mTorr，"
                f"状态={equip.get('status')}"
            )
        elif history:
            lines.append(
                f"**机台日志**：设备接口不可用，历史推断 → {history.get('history_note')}"
            )
        if recipe:
            lines.append(
                f"**工艺配方**：{recipe.get('recipe_id')}，"
                f"设定压力={recipe.get('pressure_setpoint_mtorr')}mTorr，"
                f"工艺时间={recipe.get('etch_time_sec')}s"
            )

        lines.append("")

        # 动态腔体号 + CD 偏差方向（避免硬编码）
        chamber_id = (equip or {}).get("chamber_id", "未知腔体")
        if lot_info:
            cd_delta = float(lot_info.get("cd_measured_nm", 0)) - float(
                lot_info.get("cd_target_nm", 0)
            )
            cd_issue = "CD超标" if cd_delta > 0 else "CD偏小"
        else:
            cd_issue = "CD异常"

        # —— 根因结论与建议 ——
        if conflict:
            lines.append("## 根因结论")
            lines.append(
                f"检测到配方设定压力与机台实测压力存在显著偏差，"
                f"{chamber_id} 腔体压力控制异常，导致 {cd_issue}。"
            )
            lines.append("## 建议")
            lines.append(f"1. 立即停机检查 {chamber_id} 腔体的压力传感器与节流阀；")
            lines.append("2. 对该批次产品进行复测与隔离；")
            lines.append("3. 回溯近30天关联批次，评估是否需扩大召回范围。")
        elif history and not equip:
            lines.append("## 根因结论（基于历史推断）")
            lines.append(f"设备日志不可用，依据历史数据：{history.get('history_note')}")
            lines.append("## 建议")
            lines.append("1. 优先排查关联腔体的近期维护记录；")
            lines.append("2. 联系设备工程师恢复设备接口后补充分析。")
        else:
            lines.append("## 根因结论")
            lines.append("未发现明显数据矛盾，建议人工复核。")
            lines.append("## 建议")
            lines.append("请工艺工程师结合现场情况进一步确认。")

        report = "\n".join(lines)
        self.evaluator.add_tokens(report)
        return report

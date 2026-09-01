"""
core/evaluator.py
===================
过程质量 / 资源成本 / 系统韧性 三类评估指标的收集器。

对应生产评估原则：
- 过程质量：step_count（步数上限6防死循环）、reflection_valid（反思是否发现矛盾）
- 资源成本：tool_call_count、token_cost_mock（1字符=1token）
- 系统韧性：retry_count、dead_loop_flag、timeout_handled、韧性评分、业务价值
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Evaluator:
    """收集 Agent 运行过程中的评估指标（三大维度）"""

    # —— 过程质量 ——
    step_count: int = 0                  # 已执行步数
    reflection_valid: bool = False       # Reflector 是否发现数据矛盾
    max_steps: int = 6                   # 步数上限（防死循环）

    # —— 资源成本 ——
    tool_call_count: int = 0             # 工具调用总次数
    token_cost_mock: int = 0             # 模拟 Token 消耗（1 字符 = 1 token）

    # —— 系统韧性 ——
    retry_count: int = 0                 # 工具超时后的重试次数
    dead_loop_flag: bool = False         # 死循环标记
    timeout_handled: bool = False        # 是否优雅处理了超时（自愈成功）

    # —— 死循环检测内部状态 ——
    _last_tool_signature: Optional[str] = None   # 上一次工具调用签名 "name|args_json"
    _consecutive_same_calls: int = 0             # 连续相同调用计数

    # —— 业务结果 ——
    final_report: str = ""

    # -----------------------------------------------------------------
    # 记录 API
    # -----------------------------------------------------------------
    def add_tokens(self, text: Any) -> None:
        """累加模拟 Token：每输出 1 字符算 1 token"""
        self.token_cost_mock += len(str(text))

    def record_tool_call(self, name: str, args: Dict[str, Any]) -> None:
        """记录一次工具调用，并检测死循环（连续 2 步调用同一工具且参数相同）"""
        self.tool_call_count += 1
        sig = f"{name}|{json.dumps(args, sort_keys=True, ensure_ascii=False)}"
        if sig == self._last_tool_signature:
            self._consecutive_same_calls += 1
            # 连续 2 步（即第 2 次重复）即判定死循环
            if self._consecutive_same_calls >= 1:
                self.dead_loop_flag = True
        else:
            self._consecutive_same_calls = 0
        self._last_tool_signature = sig

    # -----------------------------------------------------------------
    # 评分 / 派生指标
    # -----------------------------------------------------------------
    def resilience_score(self) -> str:
        """韧性评分：是否优雅处理超时"""
        if self.retry_count == 0:
            return "高（未触发超时）"
        if self.timeout_handled:
            return "高（已自愈）"
        return "中（已重试但未恢复）"

    def business_value(self) -> bool:
        """业务价值：最终结论是否包含'建议'二字"""
        return "建议" in self.final_report

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_count": self.step_count,
            "tool_call_count": self.tool_call_count,
            "token_cost_mock": self.token_cost_mock,
            "retry_count": self.retry_count,
            "dead_loop_flag": self.dead_loop_flag,
            "reflection_valid": self.reflection_valid,
            "timeout_handled": self.timeout_handled,
            "resilience_score": self.resilience_score(),
            "business_value": self.business_value(),
        }

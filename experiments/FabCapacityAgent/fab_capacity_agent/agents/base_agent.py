"""
FabCapacityAgent - Agent 基类 (BaseAgent)

定义统一的 PTA (Perceive-Think-Act) 循环框架:
  perceive(context)  -> 结构化感知结果 (从环境/MES抽取状态)
  think(perception)  -> 推理与决策 (分析+方案)
  act(decision)      -> 执行动作 (产出报告/调用服务/落库)
  run(context)       -> 串联 PTA 完整循环

设计原则:
  1) 所有 Agent 共享 BaseAgent 的: 名称/类型/日志/计时/状态/LLM客户端
  2) 子类只需重写 perceive/think/act, 自动获得 run() + 日志 + 异常兜底
  3) 每一步的输入/输出/耗时都通过 StepResult 记录, 供 Orchestrator 落库
  4) 所有方法都有 try-except 兜底, 单 Agent 失败不中断全链路
"""

import os
import sys
import time
import datetime as dt
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod

# 让模块可直接运行 (把项目根加入 sys.path)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.helpers import get_logger, try_except, get_config
from utils.constants import (
    AGENT_PERCEPTION, AGENT_ANALYSIS, AGENT_DECISION, AGENT_EXECUTION,
    AGENT_NAME_CN,
    STAGE_PERCEIVE, STAGE_THINK, STAGE_ACT,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_RUNNING, STATUS_PENDING,
)
from utils.llm_client import LLMClient, get_llm, PROVIDER_DEEPSEEK

logger = get_logger("BaseAgent", level="INFO")


# =============================================================================
# 步骤结果数据类
# =============================================================================

@dataclass
class StepResult:
    """单步执行结果 (perceive/think/act 各产生一个)。"""
    agent_name: str
    stage: str                                    # perceive/think/act
    status: str = STATUS_PENDING                  # success/failed/running/timeout
    duration_ms: int = 0
    input_snapshot: Any = None                    # 输入快照 (可JSON序列化)
    output_result: Any = None                     # 输出结果
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "stage": self.stage,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "input_snapshot": self.input_snapshot,
            "output_result": self.output_result,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Agent 运行上下文
# =============================================================================

@dataclass
class AgentContext:
    """
    Agent 运行上下文, 在 Orchestrator 编排时跨 Agent 传递。

    字段说明:
      run_id          - 本次全链路运行唯一ID (用于日志关联)
      trigger         - 触发源 (manual/scheduled/alert)
      user_query      - 用户原始查询 (可选)
      snapshot        - PerceptionAgent 产出的结构化快照
      analysis_report - AnalysisAgent 产出的分析报告
      decision_plan   - DecisionAgent 产出的决策方案
      execution_output- ExecutionAgent 产出的最终输出
      extra           - 自由扩展字段 (任意键值对)
    """
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    trigger: str = "manual"
    user_query: Optional[str] = None
    snapshot: Optional[Any] = None
    analysis_report: Optional[Any] = None
    decision_plan: Optional[Any] = None
    execution_output: Optional[Any] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    started_at: dt.datetime = field(default_factory=lambda: dt.datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "trigger": self.trigger,
            "user_query": self.user_query,
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "extra_keys": list(self.extra.keys()),
            "has_snapshot": self.snapshot is not None,
            "has_analysis": self.analysis_report is not None,
            "has_decision": self.decision_plan is not None,
            "has_execution": self.execution_output is not None,
        }


# =============================================================================
# BaseAgent 抽象基类
# =============================================================================

class BaseAgent(ABC):
    """
    所有 Agent 的抽象基类, 提供:
      - 统一的 PTA (Perceive-Think-Act) 循环
      - 计时 + 日志 + 异常兜底
      - LLM 客户端注入 (可选, 作为 Agent 的"大脑")
      - 步骤结果收集 (供 Orchestrator 落库)

    子类必须实现: perceive / think / act 三个方法
    """

    # 子类必须覆盖的类属性
    AGENT_TYPE: str = "base"                       # 子类覆盖: perception/analysis/decision/execution
    AGENT_NAME_CN: str = "基类Agent"

    def __init__(
        self,
        name: Optional[str] = None,
        llm: Optional[LLMClient] = None,
        use_llm: Optional[bool] = None,
    ) -> None:
        # 实例名 (默认用类属性)
        self.name: str = name or self.AGENT_TYPE
        self.agent_type: str = self.AGENT_TYPE

        # LLM "大脑" - 默认尝试创建 DeepSeek 客户端
        # use_llm=None 表示跟随配置; use_llm=False 强制关闭
        self.llm: Optional[LLMClient] = llm
        if self.llm is None and use_llm is not False:
            try:
                # 跟随 settings.yaml -> agent.<type>.use_llm 或全局配置
                cfg_use_llm = get_config(
                    "agent", f"{self.agent_type}_agent", "use_llm", default=True
                )
                if cfg_use_llm:
                    self.llm = get_llm(provider=PROVIDER_DEEPSEEK)
            except Exception as exc:
                logger.warning(f"[{self.name}] LLM初始化失败, 走纯本地模式: {exc}")
                self.llm = None

        # 步骤结果收集
        self.steps: List[StepResult] = []

        # 状态
        self.status: str = STATUS_PENDING
        self.last_duration_ms: int = 0

        # 自定义 logger (按 agent 名分通道)
        self.logger = get_logger(f"Agent[{self.name}]", level="INFO")

    # =========================================================================
    # 三个抽象方法 (子类实现)
    # =========================================================================

    @abstractmethod
    def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """
        感知阶段: 从环境/DB/上游 Agent 输出抽取结构化状态。

        Args:
            context: 运行上下文 (含历史步骤的输出)

        Returns:
            结构化感知结果 (dict), 供 think() 消费
        """
        ...

    @abstractmethod
    def think(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        思考阶段: 基于感知结果做推理/分析/方案生成。

        Args:
            perception: perceive() 的返回

        Returns:
            决策/分析结果 (dict), 供 act() 消费
        """
        ...

    @abstractmethod
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        行动阶段: 执行决策, 产出报告/落库/调用外部服务等。

        Args:
            decision: think() 的返回

        Returns:
            执行结果 (dict), 通常是给用户/前端展示的最终输出
        """
        ...

    # =========================================================================
    # PTA 循环 (统一封装, 子类无需重写)
    # =========================================================================

    def run(self, context: AgentContext) -> Dict[str, Any]:
        """
        串联完整 PTA 循环:
          1) perceive(context) -> perception
          2) think(perception) -> decision
          3) act(decision)     -> output

        每步自动: 计时 + 日志 + 异常兜底 + StepResult 落库到 self.steps

        Args:
            context: 运行上下文

        Returns:
            {"perception":..., "decision":..., "output":..., "steps":[...]}
        """
        self.logger.info(f"▶ Agent[{self.name}] 启动 PTA 循环 (run_id={context.run_id})")
        self.steps = []
        self.status = STATUS_RUNNING
        t_start = time.perf_counter()

        # ---- Step 1: Perceive ----
        perception = self._safe_step(
            stage=STAGE_PERCEIVE,
            fn=lambda: self.perceive(context),
            input_snapshot=context.to_dict(),
        )

        # ---- Step 2: Think ----
        decision = self._safe_step(
            stage=STAGE_THINK,
            fn=lambda: self.think(perception or {}),
            input_snapshot=perception,
        )

        # ---- Step 3: Act ----
        output = self._safe_step(
            stage=STAGE_ACT,
            fn=lambda: self.act(decision or {}),
            input_snapshot=decision,
        )

        # 总耗时
        self.last_duration_ms = int((time.perf_counter() - t_start) * 1000)
        self.status = STATUS_SUCCESS if all(s.status == STATUS_SUCCESS for s in self.steps) else STATUS_FAILED

        self.logger.info(
            f"✓ Agent[{self.name}] 完成 (总耗时 {self.last_duration_ms}ms, "
            f"成功 {sum(1 for s in self.steps if s.status==STATUS_SUCCESS)}/{len(self.steps)})"
        )

        return {
            "agent_name": self.name,
            "agent_type": self.agent_type,
            "run_id": context.run_id,
            "perception": perception,
            "decision": decision,
            "output": output,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration_ms": self.last_duration_ms,
            "status": self.status,
        }

    # =========================================================================
    # 单步安全执行 (统一计时 + 异常兜底)
    # =========================================================================

    def _safe_step(
        self,
        stage: str,
        fn: Callable[[], Any],
        input_snapshot: Any = None,
    ) -> Any:
        """
        安全执行单步:
          - 计时
          - try-except 兜底 (失败不中断, 返回 {} 并记录错误)
          - 自动构造 StepResult 落入 self.steps
        """
        step = StepResult(
            agent_name=self.name,
            stage=stage,
            status=STATUS_RUNNING,
            input_snapshot=self._safe_serialize(input_snapshot),
        )
        t0 = time.perf_counter()
        try:
            result = fn()
            step.status = STATUS_SUCCESS
            step.output_result = self._safe_serialize(result)
            step.duration_ms = int((time.perf_counter() - t0) * 1000)
            self.logger.info(f"  · [{stage}] 成功 ({step.duration_ms}ms)")
        except Exception as exc:
            step.status = STATUS_FAILED
            step.duration_ms = int((time.perf_counter() - t0) * 1000)
            step.error_message = f"{type(exc).__name__}: {exc}"
            self.logger.error(f"  · [{stage}] 失败 ({step.duration_ms}ms): {exc}", exc_info=True)
            result = {}
        self.steps.append(step)
        return result

    # =========================================================================
    # LLM 调用便捷封装
    # =========================================================================

    def llm_chat(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """安全调用 LLM 聊天 (LLM 不可用返回空串)。"""
        if not self.llm:
            return ""
        try:
            return self.llm.chat(prompt, system=system, **kwargs) or ""
        except Exception as exc:
            self.logger.warning(f"LLM chat 失败: {exc}")
            return ""

    def llm_json(self, prompt: str, system: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """安全调用 LLM JSON 抽取 (LLM 不可用返回 None)。"""
        if not self.llm:
            return None
        try:
            return self.llm.chat_json(prompt, system=system, **kwargs)
        except Exception as exc:
            self.logger.warning(f"LLM chat_json 失败: {exc}")
            return None

    # =========================================================================
    # 内部工具
    # =========================================================================

    @staticmethod
    def _safe_serialize(obj: Any) -> Any:
        """
        把任意对象转为可 JSON 序列化形式 (供落库/日志)。
        - dict/list/基本类型直接返回
        - dataclass -> asdict
        - pandas DataFrame -> dict records
        - 其它对象 -> str()
        """
        if obj is None:
            return None
        # 基本类型
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {str(k): BaseAgent._safe_serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [BaseAgent._safe_serialize(x) for x in obj]
        # dataclass
        if hasattr(obj, "__dataclass_fields__"):
            try:
                return BaseAgent._safe_serialize(asdict(obj))
            except Exception:
                pass
        # pandas DataFrame / Series / NaT / NaN
        try:
            import pandas as pd
            # NaT / NaN / None 标量: pd.isna 对标量也安全
            if obj is pd.NaT or (not isinstance(obj, (dict, list, tuple)) and pd.isna(obj)):
                return None
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient="records")
            if isinstance(obj, pd.Series):
                return obj.to_dict()
        except Exception:
            pass
        # datetime (注意: pd.NaT 也会 isinstance datetime 为 True, 上面已先拦截)
        if isinstance(obj, (dt.datetime, dt.date)):
            try:
                return obj.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError):
                # NaT 或无效日期
                return None
        # numpy 类型
        try:
            import numpy as np
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj) if not np.isnan(obj) else None
            if isinstance(obj, np.bool_):
                return bool(obj)
        except Exception:
            pass
        # 其它 -> 字符串
        try:
            return str(obj)
        except Exception:
            return None


# =============================================================================
# 模块自检: 用一个最简子类验证 PTA 流程
# =============================================================================

if __name__ == "__main__":
    # 一个最简 Agent 子类, 用于自检
    class DummyAgent(BaseAgent):
        AGENT_TYPE = "dummy"
        AGENT_NAME_CN = "测试Agent"

        def perceive(self, context: AgentContext) -> Dict[str, Any]:
            return {"raw_value": 42, "context_run_id": context.run_id}

        def think(self, perception: Dict[str, Any]) -> Dict[str, Any]:
            v = perception.get("raw_value", 0)
            return {"doubled": v * 2, "is_even": v % 2 == 0}

        def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": f"最终值={decision.get('doubled')}, 偶数={decision.get('is_even')}"}

    agent = DummyAgent(use_llm=False)  # 关闭 LLM, 加速自检
    ctx = AgentContext(trigger="self_test")
    result = agent.run(ctx)

    print("=== PTA 循环结果 ===")
    print(f"  Agent: {result['agent_name']} ({result['agent_type']})")
    print(f"  Run ID: {result['run_id']}")
    print(f"  总耗时: {result['total_duration_ms']}ms")
    print(f"  状态: {result['status']}")
    print(f"  Steps:")
    for s in result["steps"]:
        print(f"    - {s['stage']:>9s}  {s['status']:>7s}  {s['duration_ms']:>4d}ms  "
              f"输出={str(s['output_result'])[:60]}")
    print(f"\n  最终输出: {result['output']}")

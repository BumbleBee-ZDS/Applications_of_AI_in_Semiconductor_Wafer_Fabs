"""
FabCapacityAgent - Agent 编排器 (Orchestrator)

职责:
  按 Perception → Analysis → Decision → Execution 顺序编排 4 个 Agent
  支持两种调用模式:
    1) 全链路调用 run_full_pipeline()  - 串联4个Agent, 输出最终报告
    2) 单Agent调用 run_single(agent_type) - 只跑某一个Agent (调试/前端按需)

特性:
  - 记录每步输入输出耗时, 落库到 agent_logs (审计追踪)
  - 失败重试 (max_retries)
  - 全链路超时控制 (timeout)
  - 返回结构化 PipelineResult, 含执行图/状态/统计
"""

import os
import sys
import time
import uuid
import datetime as dt
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from agents.base_agent import BaseAgent, AgentContext, StepResult
from agents.perception_agent import PerceptionAgent
from agents.analysis_agent import AnalysisAgent
from agents.decision_agent import DecisionAgent
from agents.execution_agent import ExecutionAgent

from models.capacity import AgentLogDAO
from utils.helpers import get_logger, try_except, get_config, safe_round
from utils.constants import (
    AGENT_PERCEPTION, AGENT_ANALYSIS, AGENT_DECISION, AGENT_EXECUTION,
    AGENT_ORCHESTRATOR, AGENT_NAME_CN,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_RUNNING, STATUS_PENDING, STATUS_TIMEOUT,
)
from utils.llm_client import LLMClient

logger = get_logger("Orchestrator", level="INFO")


# =============================================================================
# 数据类: PipelineResult
# =============================================================================

@dataclass
class PipelineStep:
    """单步执行记录 (一个 Agent = 一个 PipelineStep)。"""
    agent_type: str
    agent_name_cn: str
    status: str = STATUS_PENDING
    duration_ms: int = 0
    perception: Any = None
    decision: Any = None
    output: Any = None
    error_message: Optional[str] = None
    steps_detail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PipelineResult:
    """全链路执行结果。"""
    run_id: str
    trigger: str = "manual"
    started_at: str = field(default_factory=lambda: dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    finished_at: Optional[str] = None
    total_duration_ms: int = 0
    status: str = STATUS_PENDING                  # success / partial / failed

    # 每个Agent的执行记录
    pipeline_steps: List[PipelineStep] = field(default_factory=list)

    # 最终输出 (ExecutionAgent 的 output)
    final_output: Any = None
    final_report: str = ""

    # 元信息
    user_query: Optional[str] = None
    llm_enhanced: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "trigger": self.trigger,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total_duration_ms": self.total_duration_ms,
            "status": self.status,
            "pipeline_steps": [asdict(s) for s in self.pipeline_steps],
            "final_output": self.final_output,
            "final_report": self.final_report,
            "user_query": self.user_query,
            "llm_enhanced": self.llm_enhanced,
            "error_message": self.error_message,
        }

    def summary(self) -> Dict[str, Any]:
        """精简摘要, 给前端展示用。"""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "total_duration_ms": self.total_duration_ms,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "user_query": self.user_query,
            "llm_enhanced": self.llm_enhanced,
            "steps": [
                {
                    "agent_type": s.agent_type,
                    "agent_name_cn": s.agent_name_cn,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "error": s.error_message,
                }
                for s in self.pipeline_steps
            ],
        }


# =============================================================================
# 主类: Orchestrator
# =============================================================================

class Orchestrator:
    """
    Agent 编排器。

    用法:
        orch = Orchestrator()
        result = orch.run_full_pipeline()           # 全链路
        print(result.summary())

        # 单 Agent 调用
        snap = orch.run_single(AGENT_PERCEPTION)
    """

    # 默认编排顺序
    PIPELINE_ORDER = [
        AGENT_PERCEPTION,
        AGENT_ANALYSIS,
        AGENT_DECISION,
        AGENT_EXECUTION,
    ]

    def __init__(
        self,
        perception_agent: Optional[PerceptionAgent] = None,
        analysis_agent: Optional[AnalysisAgent] = None,
        decision_agent: Optional[DecisionAgent] = None,
        execution_agent: Optional[ExecutionAgent] = None,
        llm: Optional[LLMClient] = None,
    ) -> None:
        # LLM 客户端 (统一注入到所有 Agent)
        self.llm = llm

        # 初始化四个 Agent
        self.agents: Dict[str, BaseAgent] = {
            AGENT_PERCEPTION: perception_agent or PerceptionAgent(llm=llm),
            AGENT_ANALYSIS: analysis_agent or AnalysisAgent(llm=llm),
            AGENT_DECISION: decision_agent or DecisionAgent(llm=llm),
            AGENT_EXECUTION: execution_agent or ExecutionAgent(llm=llm),
        }

        # 配置
        self.timeout_sec: int = int(
            get_config("agent", "orchestrator", "timeout", default=300)
        )
        self.max_retries: int = int(
            get_config("agent", "orchestrator", "max_retries", default=2)
        )

        # 日志 DAO
        self.log_dao = AgentLogDAO()

    # =========================================================================
    # 全链路编排
    # =========================================================================

    @try_except(default_return=PipelineResult(run_id="error", status=STATUS_FAILED))
    def run_full_pipeline(
        self,
        user_query: Optional[str] = None,
        trigger: str = "manual",
        window_hours: int = 24,
        history_days: int = 30,
    ) -> PipelineResult:
        """
        串联执行 4 个 Agent:
          Perception → Analysis → Decision → Execution

        Args:
            user_query: 用户原始查询 (可选, 会写入上下文)
            trigger: 触发源 (manual/scheduled/alert)
            window_hours: 感知窗口 (近 N 小时数据)
            history_days: 分析窗口 (近 N 天历史)

        Returns:
            PipelineResult 结构化结果
        """
        run_id = uuid.uuid4().hex[:12]
        t_start = time.perf_counter()
        result = PipelineResult(
            run_id=run_id,
            trigger=trigger,
            user_query=user_query,
        )

        # 构造上下文, 跨 Agent 传递
        context = AgentContext(
            run_id=run_id,
            trigger=trigger,
            user_query=user_query,
        )
        context.extra["window_hours"] = window_hours
        context.extra["history_days"] = history_days

        logger.info(f"{'='*60}")
        logger.info(f"🚀 全链路 Pipeline 启动 (run_id={run_id})")
        logger.info(f"  触发源: {trigger}, 用户查询: {user_query or '(无)'}")
        logger.info(f"  感知窗口: {window_hours}h, 历史窗口: {history_days}天")
        logger.info(f"{'='*60}")

        # 按顺序执行
        overall_status = STATUS_SUCCESS
        for i, agent_type in enumerate(self.PIPELINE_ORDER):
            agent = self.agents[agent_type]
            agent_name_cn = AGENT_NAME_CN.get(agent_type, agent_type)

            logger.info(f"[{i+1}/{len(self.PIPELINE_ORDER)}] ▶ {agent_name_cn}({agent_type}) 开始...")

            # 单 Agent 执行 (带重试)
            step = PipelineStep(
                agent_type=agent_type,
                agent_name_cn=agent_name_cn,
                status=STATUS_RUNNING,
            )
            t_agent_start = time.perf_counter()

            attempt = 0
            agent_result: Optional[Dict[str, Any]] = None
            last_error: Optional[str] = None

            while attempt < self.max_retries + 1:
                attempt += 1
                try:
                    agent_result = agent.run(context)
                    if agent_result.get("status") == STATUS_SUCCESS:
                        break
                    else:
                        last_error = f"Agent状态={agent_result.get('status')}"
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    logger.warning(
                        f"  {agent_name_cn} 第{attempt}次执行失败: {last_error}, "
                        f"{'重试中...' if attempt <= self.max_retries else '已耗尽重试'}"
                    )

            step.duration_ms = int((time.perf_counter() - t_agent_start) * 1000)

            if agent_result and agent_result.get("status") == STATUS_SUCCESS:
                step.status = STATUS_SUCCESS
                step.perception = agent_result.get("perception")
                step.decision = agent_result.get("decision")
                step.output = agent_result.get("output")
                step.steps_detail = agent_result.get("steps", [])

                # 把 output 写回 context, 供下一个 Agent 消费
                self._write_back_context(context, agent_type, agent_result.get("output"))

                logger.info(
                    f"  ✓ {agent_name_cn} 完成 ({step.duration_ms}ms)"
                )
            else:
                step.status = STATUS_FAILED
                step.error_message = last_error or "未知错误"
                overall_status = STATUS_FAILED if overall_status == STATUS_SUCCESS else overall_status
                logger.error(f"  ✗ {agent_name_cn} 失败: {step.error_message}")

                # 失败时也尝试写回空字典, 让后续 Agent 不至于 NPE
                self._write_back_context(context, agent_type, {})

                # 决定是否中断后续 (Perception 失败必须中断, 后面没数据可吃)
                if agent_type == AGENT_PERCEPTION:
                    logger.error("  Perception 失败, 中断后续 Agent")
                    result.status = STATUS_FAILED
                    result.error_message = f"PerceptionAgent失败: {step.error_message}"
                    break

            # 落库到 agent_logs
            self._log_to_db(
                run_id=run_id,
                agent_type=agent_type,
                step=step,
            )

            result.pipeline_steps.append(step)

            # 超时检查
            elapsed = time.perf_counter() - t_start
            if elapsed > self.timeout_sec:
                logger.error(f"  ⏱ 全链路超时 ({elapsed:.1f}s > {self.timeout_sec}s), 终止")
                result.status = STATUS_TIMEOUT
                result.error_message = f"超时 {elapsed:.1f}s"
                break

        # 最终输出
        if result.pipeline_steps and result.pipeline_steps[-1].agent_type == AGENT_EXECUTION:
            final = result.pipeline_steps[-1].output or {}
            result.final_output = final
            result.final_report = final.get("final_report", "")
            result.llm_enhanced = final.get("llm_enhanced", False)

        result.total_duration_ms = int((time.perf_counter() - t_start) * 1000)
        result.finished_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result.status = overall_status if result.status == STATUS_PENDING else result.status

        # 部分成功判定
        success_cnt = sum(1 for s in result.pipeline_steps if s.status == STATUS_SUCCESS)
        if success_cnt == 0:
            result.status = STATUS_FAILED
        elif success_cnt < len(self.PIPELINE_ORDER) and result.status == STATUS_SUCCESS:
            result.status = "partial"

        logger.info(f"{'='*60}")
        logger.info(
            f"✅ Pipeline 完成 (run_id={run_id}) | "
            f"状态={result.status} | 总耗时={result.total_duration_ms}ms | "
            f"成功 {success_cnt}/{len(result.pipeline_steps)} | "
            f"LLM增强={'✓' if result.llm_enhanced else '本地'}"
        )
        logger.info(f"{'='*60}")
        return result

    # =========================================================================
    # 单 Agent 调用
    # =========================================================================

    @try_except(default_return=None)
    def run_single(
        self,
        agent_type: str,
        user_query: Optional[str] = None,
        window_hours: int = 24,
        history_days: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        只执行单个 Agent (调试/UI按需调用)。
        对前置依赖 (snapshot/analysis/decision) 会用空数据兜底。
        """
        if agent_type not in self.agents:
            logger.error(f"未知 Agent 类型: {agent_type}")
            return None

        run_id = uuid.uuid4().hex[:12]
        context = AgentContext(
            run_id=run_id,
            trigger="single",
            user_query=user_query,
        )
        context.extra["window_hours"] = window_hours
        context.extra["history_days"] = history_days

        agent = self.agents[agent_type]
        logger.info(f"▶ 单Agent调用: {agent_type} (run_id={run_id})")
        return agent.run(context)

    # =========================================================================
    # 内部工具
    # =========================================================================

    def _write_back_context(
        self,
        context: AgentContext,
        agent_type: str,
        output: Any,
    ) -> None:
        """把 Agent 的 output 写回 context, 给下游 Agent 消费。"""
        if not isinstance(output, dict):
            return
        if agent_type == AGENT_PERCEPTION:
            context.snapshot = output
        elif agent_type == AGENT_ANALYSIS:
            context.analysis_report = output
        elif agent_type == AGENT_DECISION:
            context.decision_plan = output
        elif agent_type == AGENT_EXECUTION:
            context.execution_output = output

    def _log_to_db(
        self,
        run_id: str,
        agent_type: str,
        step: PipelineStep,
    ) -> None:
        """把单步结果落库到 agent_logs 表。"""
        try:
            import json
            self.log_dao.insert(
                run_id=run_id,
                agent_type=agent_type,
                stage="full_pipeline",
                status=step.status,
                input_snapshot={"steps_detail": step.steps_detail},
                output_result=step.output if isinstance(step.output, (dict, list)) else str(step.output),
                duration_ms=step.duration_ms,
                error_message=step.error_message,
            )
        except Exception as exc:
            logger.warning(f"日志落库失败: {exc}")


# =============================================================================
# 单例
# =============================================================================

_orchestrator_instance: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator()
    return _orchestrator_instance


# =============================================================================
# 自检
# =============================================================================

if __name__ == "__main__":
    orch = get_orchestrator()
    print(">>> 启动全链路 Pipeline (关闭 LLM 加速)...")
    # 临时关闭 LLM 以加速自检
    for a in orch.agents.values():
        a.llm = None

    result = orch.run_full_pipeline(
        user_query="分析当前产能瓶颈并给出优化建议",
        trigger="self_test",
    )

    print(f"\n=== Pipeline 摘要 ===")
    s = result.summary()
    print(f"  Run ID: {s['run_id']}")
    print(f"  状态: {s['status']}")
    print(f"  总耗时: {s['total_duration_ms']}ms")
    print(f"  LLM增强: {s['llm_enhanced']}")
    print(f"  Steps:")
    for st in s["steps"]:
        print(f"    - {st['agent_name_cn']:>8s} ({st['agent_type']:>10s})  "
              f"{st['status']:>7s}  {st['duration_ms']:>6d}ms  "
              f"{'错误: '+st['error'] if st['error'] else ''}")

    print(f"\n=== 最终报告 (前40行) ===")
    print("\n".join(result.final_report.split("\n")[:40]))

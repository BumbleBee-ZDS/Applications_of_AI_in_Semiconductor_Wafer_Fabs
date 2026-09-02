"""RL 仿真评估：启发式奖励函数 + 策略扰动（模拟探索）。

奖励函数（参考业界 RTD 派工奖励设计）：
- 利用率 utilization     权重 +1.0（区域瓶颈负载均值）
- 周期 cycle_time        权重 +0.8（派工覆盖率，覆盖率越高等效周期越短）
- 交期 otd               权重 +1.5（URGENT 批次满足率）
- 质量风险 quality_risk  权重 −2.0（风险等级归一化惩罚）
- Q-Time 违例             每次 −10.0（未覆盖的超时批次）
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

import numpy as np

PRIORITY_RANK: dict[str, int] = {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}

REWARD_WEIGHTS: dict[str, float] = {
    "utilization": 1.0,
    "cycle_time": 0.8,
    "otd": 1.5,
    "quality_risk": 2.0,
    "qtime_violation": 10.0,
}


def _risk_level_num(strategy: dict[str, Any]) -> int:
    """读取策略风险等级并转成整数（L1~L4 → 1~4）。"""
    try:
        return int(str(strategy.get("risk_level", "L2")).strip().upper().replace("L", ""))
    except (TypeError, ValueError):
        return 2


def evaluate_detailed(strategy: dict[str, Any], state: dict[str, Any]) -> dict[str, float]:
    """按启发式奖励函数评估策略，返回分解得分。

    Args:
        strategy: 调度策略（含 recommended_dispatch / risk_level）。
        state: 工厂实时状态。

    Returns:
        各维度得分与总 reward 的字典。
    """
    lots = state.get("lots", []) or []
    dispatch = strategy.get("recommended_dispatch", []) or []
    dispatched = {d.get("lot_id") for d in dispatch}

    load_values = list(state.get("bottleneck_load", {}).values())
    utilization = float(np.mean(load_values)) if load_values else 0.0

    coverage = len(dispatched) / max(len(lots), 1)
    cycle_time = coverage

    urgent_lots = [l for l in lots if l["priority"] == "URGENT"]
    otd = (
        sum(1 for l in urgent_lots if l["lot_id"] in dispatched) / max(len(urgent_lots), 1)
        if urgent_lots else 1.0
    )

    qtime_negative = [l for l in lots if l["q_time_remaining_min"] < 0]
    qtime_violations = sum(1 for l in qtime_negative if l["lot_id"] not in dispatched)

    quality_risk = (_risk_level_num(strategy) - 1) / 3.0  # L1→0.0, L4→1.0

    reward = (
        REWARD_WEIGHTS["utilization"] * utilization
        + REWARD_WEIGHTS["cycle_time"] * cycle_time
        + REWARD_WEIGHTS["otd"] * otd
        - REWARD_WEIGHTS["quality_risk"] * quality_risk
        - REWARD_WEIGHTS["qtime_violation"] * qtime_violations
    )
    return {
        "reward": round(float(reward), 3),
        "utilization": round(float(utilization), 3),
        "cycle_time": round(float(cycle_time), 3),
        "otd": round(float(otd), 3),
        "quality_risk": round(float(quality_risk), 3),
        "qtime_penalty": float(qtime_violations),
    }


def evaluate(strategy: dict[str, Any], state: dict[str, Any]) -> float:
    """计算策略的总奖励值。"""
    return evaluate_detailed(strategy, state)["reward"]


def _find_alternative_tool(state: dict[str, Any], lot_id: str, current_tool: str) -> Optional[str]:
    """为批次寻找另一台兼容且可用的设备（换线探索）。"""
    lot = next((l for l in state.get("lots", []) if l["lot_id"] == lot_id), None)
    if not lot:
        return None
    for eq in state.get("equipment", []):
        if eq["equipment_id"] == current_tool:
            continue
        if eq["status"] in ("IDLE", "RUNNING") and lot["recipe"] in eq["supported_recipes"]:
            return eq["equipment_id"]
    return None


def _propose_dispatch(state: dict[str, Any], exclude: set[str]) -> Optional[dict[str, Any]]:
    """从队列中挑一个未派工的高优先级批次补充派工（探索）。"""
    lots = sorted(
        state.get("lots", []),
        key=lambda l: (PRIORITY_RANK.get(l["priority"], 9), l["q_time_remaining_min"]),
    )
    for lot in lots:
        if lot["lot_id"] in exclude:
            continue
        tool = next(
            (e for e in state.get("equipment", [])
             if e["status"] in ("IDLE", "RUNNING") and lot["recipe"] in e["supported_recipes"]),
            None,
        )
        if tool:
            return {
                "lot_id": lot["lot_id"],
                "equipment_id": tool["equipment_id"],
                "action": "MOVE",
                "reason": "RL 探索补充派工（Q-Time/优先级）",
                "lot_priority": lot["priority"],
            }
    return None


def perturb_strategy(
    strategy: dict[str, Any],
    state: Optional[dict[str, Any]] = None,
    n_variants: int = 3,
) -> list[dict[str, Any]]:
    """生成 n 条扰动变体（模拟 RL 探索）。

    扰动方式：交换两条派工的设备 → 单条派工换线 → 补充一条新派工。

    Args:
        strategy: 基础策略（通常为 LLM 输出）。
        state: 工厂状态（用于换线/补充派工；为 None 时仅做交换）。
        n_variants: 变体数量。

    Returns:
        变体策略列表（strategy_id 带 -V1/-V2/-V3 后缀）。
    """
    base = deepcopy(strategy.get("recommended_dispatch", []) or [])
    variants: list[dict[str, Any]] = []
    for i in range(n_variants):
        variant = deepcopy(strategy)
        variant["strategy_id"] = f"{strategy.get('strategy_id', 'STRAT')}-V{i + 1}"
        variant["variant"] = f"探索变体 {i + 1}"
        disp = deepcopy(base)

        if len(disp) >= 2:
            rng = np.random.default_rng(i)
            a, b = rng.choice(len(disp), 2, replace=False)
            disp[a]["equipment_id"], disp[b]["equipment_id"] = (
                disp[b]["equipment_id"], disp[a]["equipment_id"],
            )
            disp[a]["reason"] = f"{disp[a].get('reason', '')}；RL 交换设备"
        elif disp and state:
            alt = _find_alternative_tool(state, disp[0].get("lot_id", ""), disp[0].get("equipment_id", ""))
            if alt:
                disp[0] = {**disp[0], "equipment_id": alt, "reason": f"{disp[0].get('reason', '')}；RL 换线探索"}
        elif state:
            extra = _propose_dispatch(state, exclude={d.get("lot_id") for d in disp})
            if extra:
                disp.append(extra)

        variant["recommended_dispatch"] = disp
        variants.append(variant)
    return variants


def evaluate_multiple(strategies: list[dict[str, Any]], state: dict[str, Any]) -> list[dict[str, Any]]:
    """批量评估并排序，返回最优在前的列表。

    Args:
        strategies: 候选策略列表（原始 + 扰动变体）。
        state: 工厂实时状态。

    Returns:
        每个元素含 reward 及各维度得分、strategy_id、variant、strategy 引用，按 reward 降序。
    """
    results: list[dict[str, Any]] = []
    for s in strategies:
        detail = evaluate_detailed(s, state)
        results.append({
            **detail,
            "strategy_id": s.get("strategy_id", "-"),
            "variant": s.get("variant", "LLM 原始策略"),
            "source": s.get("source", "-"),
            "strategy": s,
        })
    results.sort(key=lambda r: r["reward"], reverse=True)
    return results

"""调度 Agent：压缩工厂状态 + 诊断摘要 → DeepSeek v4-pro 生成派工策略。

策略必须满足：Q-Time 优先、Recipe 兼容、剔除 PM/DOWN/HOLD 设备、考虑
诊断建议与 PM 计划。LLM 失败时回退到启发式贪心派工。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from utils.helpers import parse_json_response
from utils.llm_client import DEEPSEEK_HEAVY_MODEL, chat_deepseek

SCHEDULING_SYSTEM_PROMPT = (
    "你是半导体 12 英寸晶圆厂 RTD（Real-Time Dispatching）实时派工系统的调度专家。\n"
    "派工必须满足以下硬约束：\n"
    "1. Q-Time：已超时（q_time_remaining_min < 0）或即将超时的批次必须最优先处理；\n"
    "2. Recipe 兼容：批次 recipe 必须在目标设备 supported_recipes 中；\n"
    "3. PM / DOWN / HOLD：状态为 PM、DOWN 或诊断建议 HOLD 的设备不可派工；\n"
    "4. 优先级：URGENT > HIGH > NORMAL > LOW；\n"
    "5. 每批最多派往一台设备，每台设备本轮最多接收一个批次。\n"
    "请基于工厂实时状态与诊断摘要输出派工策略 JSON（只输出 JSON，不要解释）：\n"
    '{"strategy_id": "STRAT-YYYYMMDD-HHMMSS", '
    '"recommended_dispatch": [{"lot_id": "...", "equipment_id": "...", "action": "MOVE|HOLD", "reason": "中文理由"}], '
    '"constraints_checked": ["Q-Time", "Recipe 兼容", "PM 计划", "HOLD 建议"], '
    '"requires_approval": true, "risk_level": "L1|L2|L3|L4", '
    '"otd_estimate_min": 120, "quality_risk_note": "中文质量风险说明"}'
)

PRIORITY_RANK: dict[str, int] = {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}


def compress_state(factory_state: dict[str, Any]) -> str:
    """把工厂状态压缩为适合 LLM 阅读的文本摘要。"""
    lines = [
        f"时间戳：{factory_state['timestamp']}",
        f"总 WIP：{factory_state['wip_total']} 片；宕机设备：{factory_state['tool_down_count']} 台；告警：{len(factory_state['alarms'])} 条",
    ]
    lines.append("【设备】")
    for eq in factory_state["equipment"]:
        lines.append(
            f"- {eq['equipment_id']}（{eq['area']}）状态={eq['status']} 当前配方={eq.get('current_recipe') or '-'} "
            f"支持配方=[{','.join(eq['supported_recipes'])}] 下一批次={eq.get('next_lot') or '-'}"
        )
    lines.append("【批次】")
    for lot in factory_state["lots"]:
        lines.append(
            f"- {lot['lot_id']} 优先级={lot['priority']} 配方={lot['recipe']} "
            f"Q-Time剩余={lot['q_time_remaining_min']}min 片数={lot['wafer_count']} HOLD={lot.get('hold', False)}"
        )
    lines.append("【区域瓶颈负载】" + "；".join(f"{k}={v:.2f}" for k, v in factory_state["bottleneck_load"].items()))
    lines.append("【PM 计划】")
    for pm in factory_state["pm_schedule"]:
        lines.append(f"- {pm['equipment_id']} {pm['pm_type']} 剩余{pm['due_in_min']}min 状态={pm['status']}")
    return "\n".join(lines)


def diagnose_summary(diagnoses: list[dict[str, Any]]) -> str:
    """把诊断报告压缩为调度可用的摘要。"""
    if not diagnoses:
        return "无异常事件，无需诊断约束。"
    lines: list[str] = []
    for d in diagnoses:
        causes = "、".join(c["cause"] for c in d["root_causes"][:2])
        lines.append(
            f"- 事件 {d['event_id']} @ {d['equipment_id']}（{d['severity']}）：根因={causes}；"
            f"质量影响={d['quality_impact']}；调度建议={d['rtd_suggestion']}；"
            f"建议HOLD={d['hold_equipment']}；需人工确认={d['human_confirmation_required']}"
        )
    return "\n".join(lines)


def heuristic_strategy(factory_state: dict[str, Any], diagnoses: list[dict[str, Any]]) -> dict[str, Any]:
    """规则启发式派工（LLM 不可用时的降级策略）。"""
    hold_tools = {d["equipment_id"] for d in diagnoses if d.get("hold_equipment")}
    lots = factory_state["lots"]
    ordered = sorted(
        lots,
        key=lambda lot: (
            int(lot["q_time_remaining_min"] < 0),
            PRIORITY_RANK.get(lot["priority"], 9),
            lot["q_time_remaining_min"],
        ),
    )
    available = [
        eq for eq in factory_state["equipment"]
        if eq["status"] in ("IDLE", "RUNNING") and eq["equipment_id"] not in hold_tools
    ]
    dispatch: list[dict[str, Any]] = []
    used_tools: set[str] = set()
    for lot in ordered:
        if lot.get("hold"):
            continue
        tool = next(
            (eq for eq in available if eq["equipment_id"] not in used_tools and lot["recipe"] in eq["supported_recipes"]),
            None,
        )
        if tool is None:
            continue
        used_tools.add(tool["equipment_id"])
        parts = [f"{lot['priority']} 优先级"]
        if lot["q_time_remaining_min"] < 0:
            parts.append("Q-Time 已超时，紧急派工")
        else:
            parts.append(f"Q-Time 剩余 {int(lot['q_time_remaining_min'])}min")
        dispatch.append({
            "lot_id": lot["lot_id"],
            "equipment_id": tool["equipment_id"],
            "action": "MOVE",
            "reason": "，".join(parts),
            "lot_priority": lot["priority"],
        })

    has_urgent = any(l["priority"] == "URGENT" for l in lots)
    qtime_negative = sum(1 for l in lots if l["q_time_remaining_min"] < 0)
    return {
        "strategy_id": f"STRAT-{datetime.now():%Y%m%d-%H%M%S}-H",
        "recommended_dispatch": dispatch,
        "constraints_checked": ["Q-Time 违例检查", "Recipe 与设备能力匹配", "PM / DOWN / HOLD 设备剔除", "高优先级批次优先"],
        "requires_approval": bool(has_urgent or qtime_negative),
        "risk_level": "L3" if (has_urgent or qtime_negative) else "L2",
        "otd_estimate_min": int(60 + len(dispatch) * 15 + (30 if qtime_negative else 0)),
        "quality_risk_note": (
            "注意：部分设备处于诊断 HOLD 状态，已从候选派工设备中剔除。" if hold_tools
            else "启发式策略优先处置 Q-Time 违例与高优先级批次，未发现设备 HOLD 冲突。"
        ),
        "source": "启发式规则（heuristic）",
    }


def _normalize_strategy(data: dict[str, Any], factory_state: dict[str, Any]) -> dict[str, Any]:
    """清洗 LLM 输出：补齐字段、注入 lot_priority、归一化 otd 为整数。"""
    priority_map = {lot["lot_id"]: lot["priority"] for lot in factory_state["lots"]}
    raw_dispatch = data.get("recommended_dispatch") or []
    dispatch: list[dict[str, Any]] = []
    for d in raw_dispatch:
        if not isinstance(d, dict):
            continue
        lot_id = str(d.get("lot_id", ""))
        dispatch.append({
            "lot_id": lot_id,
            "equipment_id": str(d.get("equipment_id", "")),
            "action": str(d.get("action", "MOVE")),
            "reason": str(d.get("reason", "")),
            "lot_priority": priority_map.get(lot_id, "NORMAL"),
        })
    try:
        otd = int(data.get("otd_estimate_min", 120))
    except (TypeError, ValueError):
        otd = 120
    return {
        "strategy_id": str(data.get("strategy_id") or f"STRAT-{datetime.now():%Y%m%d-%H%M%S}"),
        "recommended_dispatch": dispatch,
        "constraints_checked": [str(c) for c in (data.get("constraints_checked") or [])],
        "requires_approval": bool(data.get("requires_approval", False)),
        "risk_level": str(data.get("risk_level") or "L2"),
        "otd_estimate_min": otd,
        "quality_risk_note": str(data.get("quality_risk_note") or ""),
        "source": DEEPSEEK_HEAVY_MODEL,
    }


def build_strategy(factory_state: dict[str, Any], diagnoses: list[dict[str, Any]]) -> dict[str, Any]:
    """生成派工策略（LLM 优先，失败降级启发式）。

    Args:
        factory_state: 工厂实时状态。
        diagnoses: 诊断报告列表。

    Returns:
        策略字典：strategy_id / recommended_dispatch / constraints_checked /
        requires_approval / risk_level / otd_estimate_min / quality_risk_note。
    """
    user_prompt = f"## 工厂实时状态\n{compress_state(factory_state)}\n\n## 诊断摘要\n{diagnose_summary(diagnoses)}"
    try:
        text = chat_deepseek(
            messages=[
                {"role": "system", "content": SCHEDULING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=DEEPSEEK_HEAVY_MODEL,
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        return _normalize_strategy(parse_json_response(text), factory_state)
    except Exception as exc:
        strategy = heuristic_strategy(factory_state, diagnoses)
        strategy["llm_error"] = str(exc)[:200]
        return strategy

"""诊断 Agent：千问 RAG 检索 + DeepSeek 强模型根因分析。

对感知 Agent 输出的每个事件：
1. 用千问 Embedding 检索工艺知识库 Top-3；
2. 拼接 system + user 提示词调用 DeepSeek v4-pro（response_format=json_object）；
3. 容错解析 JSON（剥离 ```json 围栏）；
4. 任何异常（无 Key / 网络 / JSON 解析）时回退到规则式诊断。
"""

from __future__ import annotations

from typing import Any

import numpy as np

from utils import knowledge_base
from utils.helpers import now_iso, parse_json_response
from utils.llm_client import DEEPSEEK_HEAVY_MODEL, chat_deepseek

DIAGNOSIS_SYSTEM_PROMPT = (
    "你是半导体 12 英寸晶圆厂的高级设备与工艺工程师，服务于 RTD（Real-Time Dispatching）"
    "实时派工系统。请基于「实时事件 + 检索到的工艺知识库」进行根因诊断，输出结构化 JSON。注意：\n"
    "1. 只输出 JSON，不要输出任何解释文字；\n"
    "2. root_causes 中每条 cause 需给出 0~1 的 confidence；\n"
    "3. hold_equipment 表示是否需要将该设备置 HOLD（停止进片）。"
)

# 事件类型 → 规则降级诊断根因
_FALLBACK_CAUSES: dict[str, str] = {
    "temperature_drift": "加热器 PID 参数漂移或热电偶老化，导致腔体温度偏离配方中心",
    "pressure_anomaly": "MFC 流量漂移或真空泵能力下降，导致腔体压力偏离设定值",
    "endpoint_miss": "OES 探头污染或信号基线漂移，导致终点检测信号丢失",
    "overlay_error": "机台 stage 定位漂移或晶圆加热效应，导致 Overlay 超差",
    "tool_down": "设备硬件故障导致宕机，需维修工程师现场处理",
    "pm_overdue": "PM 计划未按期执行，设备维护窗口超期",
    "particle_risk": "腔体颗粒累积，存在缺陷率上升风险",
    "qtime_risk": "批次 Q-Time 即将/已经超时，存在批次报废风险",
    "equipment_alarm": "设备显式告警，具体根因需结合 FDC 数据进一步确认",
}

# 建议置 HOLD 的事件类型
_HOLD_TYPES: set[str] = {
    "temperature_drift", "pressure_anomaly", "endpoint_miss",
    "overlay_error", "tool_down", "pm_overdue",
}


def _fallback_diagnosis(event: dict[str, Any], kb_hits: list[tuple[dict[str, str], float]]) -> dict[str, Any]:
    """规则式降级诊断（无 API Key / LLM 调用失败时使用）。"""
    event_type = event["event_type"]
    doc = kb_hits[0][0] if kb_hits else None
    return {
        "root_causes": [{"cause": _FALLBACK_CAUSES.get(event_type, "需结合 FDC 数据人工确认"), "confidence": 0.55}],
        "quality_impact": "可能影响关键工艺参数（膜厚/线宽/均匀性等），存在良率损失风险",
        "rtd_suggestion": f"RTD 建议：{doc['content'][:150]}..." if doc else "RTD 建议：暂停进片并通知工程团队复核",
        "human_confirmation_required": event["severity"] in ("HIGH", "CRITICAL"),
        "hold_equipment": event_type in _HOLD_TYPES,
    }


def diagnose_events(events: list[dict[str, Any]], top_k: int = 3) -> list[dict[str, Any]]:
    """对事件列表逐一执行 RAG + LLM 根因诊断。

    Args:
        events: 感知 Agent 输出的标准化事件列表。
        top_k: RAG 检索条数（默认 Top-3）。

    Returns:
        诊断结果列表，每个包含 root_causes / quality_impact / rtd_suggestion /
        human_confirmation_required / hold_equipment / retrieved_kb / confidence_avg。
    """
    diagnoses: list[dict[str, Any]] = []
    for event in events:
        query = f"{event['event_type']} {event['equipment_id']} {event['description']}"
        kb_hits = knowledge_base.retrieve(query, top_k=top_k)
        kb_text = "\n".join(
            f"[{doc['doc_id']}] {doc['title']}：{doc['content']}" for doc, _score in kb_hits
        )
        user_prompt = f"""## 实时事件
{event}
## 检索到的工艺知识（RAG Top-{len(kb_hits)}）
{kb_text if kb_text else "（无检索结果）"}
请输出如下 JSON（key 名严格一致，只输出 JSON）：
{{
  "root_causes": [{{"cause": "根因描述", "confidence": 0.9}}],
  "quality_impact": "对产品质量的潜在影响",
  "rtd_suggestion": "RTD 系统应采取的调度动作建议",
  "human_confirmation_required": true,
  "hold_equipment": false
}}"""
        try:
            text = chat_deepseek(
                messages=[
                    {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=DEEPSEEK_HEAVY_MODEL,
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=1500,
            )
            data = parse_json_response(text)
        except Exception as exc:  # 无 Key / 网络 / 解析失败 → 规则降级
            data = _fallback_diagnosis(event, kb_hits)
            data["_fallback_reason"] = str(exc)[:200]

        root_causes = data.get("root_causes") or [{"cause": "待人工确认", "confidence": 0.5}]
        confidence_avg = float(
            np.mean([float(c.get("confidence", 0.5)) for c in root_causes])
        ) if root_causes else 0.5

        diagnoses.append({
            "event_id": event["event_id"],
            "equipment_id": event["equipment_id"],
            "event_type": event["event_type"],
            "severity": event["severity"],
            "description": event["description"],
            "root_causes": root_causes,
            "quality_impact": data.get("quality_impact", "待评估"),
            "rtd_suggestion": data.get("rtd_suggestion", "待评估"),
            "human_confirmation_required": bool(data.get("human_confirmation_required", True)),
            "hold_equipment": bool(data.get("hold_equipment", False)),
            "retrieved_kb": [
                {"doc_id": doc["doc_id"], "title": doc["title"], "category": doc["category"], "score": round(score, 4)}
                for doc, score in kb_hits
            ],
            "confidence_avg": round(confidence_avg, 3),
            "fallback_reason": data.get("_fallback_reason", ""),
            "timestamp": now_iso(),
        })
    return diagnoses

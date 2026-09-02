"""感知 Agent：扫描设备实时参数与显式告警，输出标准化异常事件。

检测规则（阈值）：
- 温度漂移：偏离配方中心 ≥0.5°C（≥1.0°C 视为 HIGH）；
- 压力异常：偏离配方中心 ≥15%（≥25% 视为 HIGH）；
- Overlay：量测值超出规格限；
- EPD：终点检测信号过低（<0.3）；
- 显式告警：直接转化为事件（与参数扫描去重）；
- Q-Time 风险：批次剩余时间 <30min（<0 视为 HIGH）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# 事件类型 → 建议动作（中文，供人/LLM 参考）
SUGGESTED_ACTIONS: dict[str, str] = {
    "temperature_drift": "暂停进片并通知工艺工程师复核温控（PID/热电偶），必要时空炉补偿后复机",
    "pressure_anomaly": "停止进片，检查 MFC / 真空泵 / 节气阀，执行 30 分钟泄漏率测试",
    "endpoint_miss": "立即暂停刻蚀，检查 OES 探头与窗口污染，用测试片验证终点判定",
    "overlay_error": "冻结受影响批次，执行机台对准校准（align/recalibrate），评估返工",
    "tool_down": "通知维修工程师，触发产能再平衡与批次转移评估",
    "pm_overdue": "禁止派工，立即安排 PM 并执行 qual run 验证",
    "particle_risk": "加强监控，必要时安排腔体清洁",
    "qtime_risk": "立即优先派工，超时批次转 HOLD 评估报废风险",
    "equipment_alarm": "人工确认告警并执行相应 SOP",
}

# 显式告警 code → 事件类型
ALARM_TYPE_MAP: dict[str, str] = {
    "TEMP_DRIFT": "temperature_drift",
    "PRESS_DEV": "pressure_anomaly",
    "EPD_MISS": "endpoint_miss",
    "OVERLAY_ERR": "overlay_error",
    "TOOL_DOWN": "tool_down",
    "PM_OVERDUE": "pm_overdue",
    "PARTICLE_UP": "particle_risk",
}

SEVERITY_ORDER: dict[str, int] = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _new_event(
    seq: int,
    event_type: str,
    severity: str,
    equipment_id: str,
    description: str,
    raw_parameters: dict[str, Any],
    current_lot: str | None,
) -> dict[str, Any]:
    """构造一条标准化事件。"""
    return {
        "event_id": f"EVT-{datetime.now():%H%M%S}-{seq:03d}",
        "event_type": event_type,
        "severity": severity,
        "equipment_id": equipment_id,
        "description": description,
        "raw_parameters": raw_parameters,
        "current_lot": current_lot,
        "suggested_action": SUGGESTED_ACTIONS.get(event_type, "人工确认后按 SOP 处理"),
    }


def perceive(factory_state: dict[str, Any]) -> list[dict[str, Any]]:
    """扫描工厂状态，输出标准化异常事件列表。

    Args:
        factory_state: :func:`data.factory_simulator.generate_factory_state` 的输出。

    Returns:
        事件列表，按严重程度排序，每条含 event_id / event_type / severity /
        equipment_id / description / raw_parameters / current_lot / suggested_action。
    """
    events: list[dict[str, Any]] = []
    seq = 0
    found: set[tuple[str, str]] = set()  # (equipment_id, event_type) 去重

    # ---------- 1. 设备参数阈值扫描 ----------
    for eq in factory_state.get("equipment", []):
        eid: str = eq["equipment_id"]
        params: dict[str, Any] = eq.get("params", {}) or {}
        nominal: dict[str, Any] = eq.get("nominal", {}) or {}
        spec: dict[str, Any] = eq.get("recipe_spec", {}) or {}
        current_lot: str | None = eq.get("next_lot")

        if eq["status"] == "RUNNING" and eq.get("current_recipe"):
            # 温度漂移：偏离 ≥0.5°C
            temp_now = params.get("temperature_c")
            temp_center = nominal.get("temperature_c")
            if temp_now is not None and temp_center is not None:
                dev = float(temp_now) - float(temp_center)
                limit = float(spec.get("temp_limit_c", 0.5))
                if abs(dev) >= limit:
                    seq += 1
                    found.add((eid, "temperature_drift"))
                    events.append(_new_event(
                        seq, "temperature_drift",
                        "HIGH" if abs(dev) >= 1.0 else "MEDIUM",
                        eid,
                        f"{eid} 当前温度 {temp_now}°C，偏离配方中心 {temp_center}°C（阈值 ±{limit}°C）",
                        {"temperature_c": temp_now, "nominal_c": temp_center, "deviation_c": round(dev, 2)},
                        current_lot,
                    ))
            # 压力异常：偏离 ≥15%
            press_now = params.get("pressure_torr")
            press_center = nominal.get("pressure_torr")
            if press_now is not None and press_center is not None:
                dev_pct = (float(press_now) - float(press_center)) / float(press_center)
                limit = float(spec.get("pressure_limit_pct", 0.15))
                if abs(dev_pct) >= limit:
                    seq += 1
                    found.add((eid, "pressure_anomaly"))
                    events.append(_new_event(
                        seq, "pressure_anomaly",
                        "HIGH" if abs(dev_pct) >= 0.25 else "MEDIUM",
                        eid,
                        f"{eid} 当前压力 {press_now} torr，偏离配方中心 {dev_pct:.1%}（阈值 ±{limit:.0%}）",
                        {"pressure_torr": press_now, "nominal_torr": press_center, "deviation_pct": round(dev_pct, 4)},
                        current_lot,
                    ))
            # Overlay 超差
            overlay_limit = spec.get("overlay_limit_nm")
            overlay_now = params.get("overlay_nm")
            if overlay_limit is not None and overlay_now is not None and float(overlay_now) > float(overlay_limit):
                seq += 1
                found.add((eid, "overlay_error"))
                events.append(_new_event(
                    seq, "overlay_error",
                    "CRITICAL" if float(overlay_now) > float(overlay_limit) * 2 else "HIGH",
                    eid,
                    f"{eid} Overlay 量测 {overlay_now}nm，超出规格 {overlay_limit}nm",
                    {"overlay_nm": overlay_now, "overlay_limit_nm": overlay_limit},
                    current_lot,
                ))
            # EPD 信号丢失
            epd_center = nominal.get("epd_signal")
            epd_now = params.get("epd_signal")
            if epd_center is not None and epd_now is not None and float(epd_now) < 0.3:
                seq += 1
                found.add((eid, "endpoint_miss"))
                events.append(_new_event(
                    seq, "endpoint_miss", "HIGH",
                    eid,
                    f"{eid} EPD 信号过低（{epd_now}），终点检测可能丢失，存在过蚀刻风险",
                    {"epd_signal": epd_now},
                    current_lot,
                ))

    # ---------- 2. 显式告警转化（与参数扫描去重） ----------
    for alarm in factory_state.get("alarms", []):
        eid = str(alarm.get("equipment_id", ""))
        event_type = ALARM_TYPE_MAP.get(str(alarm.get("code", "")), "equipment_alarm")
        if (eid, event_type) in found:
            continue
        seq += 1
        found.add((eid, event_type))
        eq = next((e for e in factory_state.get("equipment", []) if e["equipment_id"] == eid), None)
        events.append(_new_event(
            seq, event_type,
            str(alarm.get("severity", "MEDIUM")),
            eid,
            str(alarm.get("message", "设备显式告警")),
            {"alarm_id": alarm.get("alarm_id"), "code": alarm.get("code"), "timestamp": alarm.get("timestamp")},
            eq.get("next_lot") if eq else None,
        ))

    # ---------- 3. Q-Time 风险（批次维度） ----------
    for lot in factory_state.get("lots", []):
        qtime = float(lot.get("q_time_remaining_min", 0))
        if qtime < 30:
            seq += 1
            events.append(_new_event(
                seq, "qtime_risk",
                "HIGH" if qtime < 0 else "MEDIUM",
                "FAB-QUEUE",
                f"批次 {lot['lot_id']}（{lot['priority']}）Q-Time 剩余 {qtime:.0f}min"
                + ("，已超时，存在批次报废风险" if qtime < 0 else "，接近超时"),
                {"lot_id": lot["lot_id"], "q_time_remaining_min": qtime, "priority": lot["priority"], "recipe": lot["recipe"]},
                lot["lot_id"],
            ))

    # 按严重程度排序
    events.sort(key=lambda ev: SEVERITY_ORDER.get(ev["severity"], 9))
    return events

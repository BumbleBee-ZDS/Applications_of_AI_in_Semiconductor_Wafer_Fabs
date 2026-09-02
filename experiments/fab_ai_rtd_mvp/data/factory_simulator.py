"""晶圆厂实时数据模拟器。

模拟 12 英寸晶圆厂的关键实时信号：设备状态、批次（Lot）WIP、告警、
PM 计划、区域瓶颈负载。支持注入 4 种工艺异常（temperature_drift /
pressure_anomaly / endpoint_miss / overlay_error），用于驱动 LLM Agent
全链路（感知 → 诊断 → 调度 → RL → 执行）演示。

每次调用 :func:`generate_factory_state`（seed=None）都会得到一组不同的
设备状态与 Lot 组合，模拟"实时刷新"效果。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import numpy as np

# ---------- 异常场景标签（UI 下拉框使用） ----------
ANOMALY_LABELS: dict[str, str] = {
    "none": "✅ 无异常（随机刷新）",
    "temperature_drift": "🌡 CVD 温度漂移",
    "pressure_anomaly": "⏱ CVD 压力异常",
    "endpoint_miss": "🎯 刻蚀 EPD 丢失",
    "overlay_error": "📐 光刻 Overlay 超差",
}

# ---------- 设备定义（8 台，覆盖 4 大区域） ----------
TOOL_DEFS: list[dict[str, Any]] = [
    {"equipment_id": "CVD-001", "type": "CVD", "area": "薄膜", "recipes": ["W-DEP", "SiN-DEP"]},
    {"equipment_id": "CVD-003", "type": "CVD", "area": "薄膜", "recipes": ["OX-DEP", "W-DEP"]},
    {"equipment_id": "CVD-005", "type": "CVD", "area": "薄膜", "recipes": ["SiN-DEP", "OX-DEP"]},
    {"equipment_id": "LITHO-101", "type": "LITHO", "area": "光刻", "recipes": ["LITHO-EXP"]},
    {"equipment_id": "LITHO-102", "type": "LITHO", "area": "光刻", "recipes": ["LITHO-EXP"]},
    {"equipment_id": "ETCH-201", "type": "ETCH", "area": "刻蚀", "recipes": ["ETCH-W", "ETCH-OX"]},
    {"equipment_id": "ETCH-204", "type": "ETCH", "area": "刻蚀", "recipes": ["ETCH-W"]},
    {"equipment_id": "CMP-301", "type": "CMP", "area": "平坦化", "recipes": ["CMP-OX"]},
]

# ---------- 配方名义工艺参数与检测阈值 ----------
RECIPE_SPECS: dict[str, dict[str, Any]] = {
    "W-DEP":     {"area": "薄膜",   "nominal": {"temperature_c": 420.0, "pressure_torr": 5.0},  "temp_limit_c": 0.5, "pressure_limit_pct": 0.15},
    "OX-DEP":    {"area": "薄膜",   "nominal": {"temperature_c": 650.0, "pressure_torr": 3.0},  "temp_limit_c": 0.5, "pressure_limit_pct": 0.15},
    "SiN-DEP":   {"area": "薄膜",   "nominal": {"temperature_c": 520.0, "pressure_torr": 4.0},  "temp_limit_c": 0.5, "pressure_limit_pct": 0.15},
    "LITHO-EXP": {"area": "光刻",   "nominal": {"overlay_nm": 3.0},                             "overlay_limit_nm": 3.0},
    "ETCH-W":    {"area": "刻蚀",   "nominal": {"epd_signal": 1.0, "pressure_torr": 30.0},      "pressure_limit_pct": 0.15},
    "ETCH-OX":   {"area": "刻蚀",   "nominal": {"epd_signal": 1.0, "pressure_torr": 28.0},      "pressure_limit_pct": 0.15},
    "CMP-OX":    {"area": "平坦化", "nominal": {"pad_life_pct": 85.0}},
}

# ---------- 批次模板（8 个 Lot，含 1 个 URGENT、2 个 Q-Time 已超时） ----------
LOT_TEMPLATES: list[dict[str, Any]] = [
    {"lot_id": "LOT-A-101", "priority": "URGENT", "recipe": "W-DEP",    "area": "薄膜",   "current_step": "OP-120", "wafer_count": 25, "q_time_remaining_min": 12},
    {"lot_id": "LOT-A-102", "priority": "HIGH",   "recipe": "OX-DEP",   "area": "薄膜",   "current_step": "OP-118", "wafer_count": 25, "q_time_remaining_min": 35},
    {"lot_id": "LOT-B-201", "priority": "HIGH",   "recipe": "LITHO-EXP", "area": "光刻",  "current_step": "OP-210", "wafer_count": 25, "q_time_remaining_min": -8},
    {"lot_id": "LOT-B-202", "priority": "NORMAL", "recipe": "LITHO-EXP", "area": "光刻",  "current_step": "OP-205", "wafer_count": 25, "q_time_remaining_min": 60},
    {"lot_id": "LOT-C-301", "priority": "NORMAL", "recipe": "ETCH-W",   "area": "刻蚀",   "current_step": "OP-310", "wafer_count": 25, "q_time_remaining_min": 90},
    {"lot_id": "LOT-C-302", "priority": "LOW",    "recipe": "ETCH-OX",  "area": "刻蚀",   "current_step": "OP-308", "wafer_count": 25, "q_time_remaining_min": -20},
    {"lot_id": "LOT-D-401", "priority": "HIGH",   "recipe": "CMP-OX",   "area": "平坦化", "current_step": "OP-410", "wafer_count": 25, "q_time_remaining_min": 20},
    {"lot_id": "LOT-D-402", "priority": "NORMAL", "recipe": "CMP-OX",   "area": "平坦化", "current_step": "OP-412", "wafer_count": 25, "q_time_remaining_min": 150},
]

PRIORITY_RANK: dict[str, int] = {"URGENT": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}


def _set_running_recipe(eq: dict[str, Any], recipe: str) -> None:
    """把设备置为 RUNNING 并装载指定配方（参数取配方名义中心值）。"""
    spec = RECIPE_SPECS[recipe]
    eq["status"] = "RUNNING"
    eq["current_recipe"] = recipe
    eq["recipe_spec"] = spec
    eq["nominal"] = spec["nominal"]
    eq["params"] = {key: round(float(center), 3) for key, center in spec["nominal"].items()}


def _random_equipment(rng: np.random.Generator) -> list[dict[str, Any]]:
    """随机生成设备实时状态（RUNNING/IDLE/DOWN/PM + 传感器噪声）。"""
    equipment: list[dict[str, Any]] = []
    for tdef in TOOL_DEFS:
        status = str(rng.choice(["RUNNING", "IDLE", "DOWN", "PM"], p=[0.5, 0.25, 0.12, 0.13]))
        recipe: Optional[str] = None
        params: dict[str, float] = {}
        spec: dict[str, Any] = {}
        if status in ("RUNNING", "IDLE"):
            recipe = str(tdef["recipes"][int(rng.integers(0, len(tdef["recipes"])))])
            spec = RECIPE_SPECS[recipe]
            for key, center in spec["nominal"].items():
                if "temperature" in key:
                    params[key] = round(float(center + rng.normal(0, 0.15)), 2)      # ±0.15°C 噪声
                elif "epd" in key:
                    params[key] = round(float(min(1.0, max(0.0, center + rng.normal(0, 0.03)))), 3)
                else:
                    params[key] = round(float(center * (1.0 + rng.normal(0, 0.02))), 2)  # ±2% 噪声
        equipment.append({
            "equipment_id": tdef["equipment_id"],
            "type": tdef["type"],
            "area": tdef["area"],
            "status": status,
            "current_recipe": recipe,
            "supported_recipes": list(tdef["recipes"]),
            "params": params,
            "nominal": dict(spec.get("nominal", {})),
            "recipe_spec": spec,
            "uptime_min": int(rng.integers(120, 28800)),
            "pm_due_min": int(rng.integers(0, 1500)),
            "next_lot": None,
        })
    return equipment


def _random_lots(rng: np.random.Generator) -> list[dict[str, Any]]:
    """随机洗牌批次，并给少量批次打上 HOLD 标记（URGENT 批次永不 HOLD）。"""
    lots = [dict(t) for t in LOT_TEMPLATES]
    rng.shuffle(lots)
    for lot in lots:
        lot["hold"] = False
        if lot["lot_id"] != "LOT-A-101" and rng.random() < 0.10:
            lot["hold"] = True
    return lots


def _assign_next_lot(equipment: list[dict[str, Any]], lots: list[dict[str, Any]]) -> None:
    """把高优先级批次指派为设备的下一批次（按配方兼容匹配）。"""
    used: set[str] = set()
    for lot in sorted(lots, key=lambda l: PRIORITY_RANK.get(l["priority"], 9)):
        for eq in equipment:
            if eq["equipment_id"] in used:
                continue
            if lot["recipe"] in eq["supported_recipes"]:
                eq["next_lot"] = lot["lot_id"]
                used.add(eq["equipment_id"])
                break


def _pm_schedule(rng: np.random.Generator, equipment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """生成 PM 计划（部分可能已逾期 / 临期）。"""
    schedule: list[dict[str, Any]] = []
    for idx, eq in enumerate(equipment):
        due = int(rng.integers(-60, 720))
        status = "OVERDUE" if due < 0 else ("DUE" if due < 120 else "SCHEDULED")
        schedule.append({
            "equipment_id": eq["equipment_id"],
            "pm_type": "PM-1 月度保养" if idx % 2 == 0 else "PM-2 季度保养",
            "due_in_min": due,
            "duration_min": 120 if idx % 2 == 0 else 480,
            "status": status,
        })
    return schedule


def _random_alarms(
    rng: np.random.Generator,
    equipment: list[dict[str, Any]],
    pm_schedule: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """生成常规告警：宕机告警 + PM 逾期告警 + 随机颗粒告警。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alarms: list[dict[str, Any]] = []
    seq = 0
    for eq in equipment:
        if eq["status"] == "DOWN":
            seq += 1
            alarms.append({
                "alarm_id": f"ALM-{seq:03d}",
                "equipment_id": eq["equipment_id"],
                "severity": "HIGH",
                "code": "TOOL_DOWN",
                "message": f"{eq['equipment_id']} 设备宕机，等待维修工程师",
                "timestamp": ts,
            })
    for pm in pm_schedule:
        if pm["status"] == "OVERDUE":
            seq += 1
            alarms.append({
                "alarm_id": f"ALM-{seq:03d}",
                "equipment_id": pm["equipment_id"],
                "severity": "MEDIUM",
                "code": "PM_OVERDUE",
                "message": f"{pm['equipment_id']} {pm['pm_type']} 已逾期，禁止派工",
                "timestamp": ts,
            })
    if rng.random() < 0.3:
        candidates = [e for e in equipment if e["status"] in ("RUNNING", "IDLE")]
        if candidates:
            eq = candidates[int(rng.integers(0, len(candidates)))]
            seq += 1
            alarms.append({
                "alarm_id": f"ALM-{seq:03d}",
                "equipment_id": eq["equipment_id"],
                "severity": "MEDIUM",
                "code": "PARTICLE_UP",
                "message": f"{eq['equipment_id']} 腔体颗粒计数上升，建议密切监控",
                "timestamp": ts,
            })
    return alarms


def _apply_anomaly(anomaly: str, equipment: list[dict[str, Any]], alarms: list[dict[str, Any]]) -> None:
    """注入指定的工艺异常（覆盖设备参数并追加显式告警）。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def find(tool_id: str) -> dict[str, Any]:
        return next(e for e in equipment if e["equipment_id"] == tool_id)

    if anomaly == "temperature_drift":
        eq = find("CVD-001")
        _set_running_recipe(eq, "W-DEP")
        eq["params"]["temperature_c"] = round(eq["nominal"]["temperature_c"] + 1.2, 2)  # 偏离 +1.2°C
        eq["next_lot"] = "LOT-A-101"
        alarms.append({
            "alarm_id": f"ALM-{len(alarms) + 1:03d}",
            "equipment_id": eq["equipment_id"],
            "severity": "MEDIUM",
            "code": "TEMP_DRIFT",
            "message": f"{eq['equipment_id']} 温度偏离配方中心 +1.2°C，触发温控漂移告警",
            "timestamp": ts,
        })
    elif anomaly == "pressure_anomaly":
        eq = find("CVD-003")
        _set_running_recipe(eq, "OX-DEP")
        eq["params"]["pressure_torr"] = round(eq["nominal"]["pressure_torr"] * 1.22, 2)  # 偏离 +22%
        eq["next_lot"] = "LOT-A-102"
        alarms.append({
            "alarm_id": f"ALM-{len(alarms) + 1:03d}",
            "equipment_id": eq["equipment_id"],
            "severity": "MEDIUM",
            "code": "PRESS_DEV",
            "message": f"{eq['equipment_id']} 压力偏离配方中心 +22%（阈值 ±15%），触发压力异常告警",
            "timestamp": ts,
        })
    elif anomaly == "endpoint_miss":
        eq = find("ETCH-201")
        _set_running_recipe(eq, "ETCH-W")
        eq["params"]["epd_signal"] = 0.05  # EPD 信号近乎丢失
        eq["next_lot"] = "LOT-C-301"
        alarms.append({
            "alarm_id": f"ALM-{len(alarms) + 1:03d}",
            "equipment_id": eq["equipment_id"],
            "severity": "HIGH",
            "code": "EPD_MISS",
            "message": f"{eq['equipment_id']} 刻蚀终点检测（EPD）信号丢失，存在过蚀刻风险",
            "timestamp": ts,
        })
    elif anomaly == "overlay_error":
        eq = find("LITHO-101")
        _set_running_recipe(eq, "LITHO-EXP")
        eq["params"]["overlay_nm"] = 9.2  # 规格 3.0nm，超差 3 倍以上
        eq["next_lot"] = "LOT-B-201"
        alarms.append({
            "alarm_id": f"ALM-{len(alarms) + 1:03d}",
            "equipment_id": eq["equipment_id"],
            "severity": "HIGH",
            "code": "OVERLAY_ERR",
            "message": f"{eq['equipment_id']} 光刻 Overlay 量测 {eq['params']['overlay_nm']}nm，超出规格 3.0nm",
            "timestamp": ts,
        })


def generate_factory_state(force_anomaly: Optional[str] = None, seed: Optional[int] = None) -> dict[str, Any]:
    """生成一帧工厂实时状态。

    Args:
        force_anomaly: 可选异常场景名，见 :data:`ANOMALY_LABELS`。
        seed: 随机种子（None 表示每次刷新结果不同）。

    Returns:
        完整 factory_state 字典，包含 timestamp / equipment / lots / alarms /
        pm_schedule / bottleneck_load / wip_total / tool_down_count。
    """
    rng = np.random.default_rng(seed)
    equipment = _random_equipment(rng)
    lots = _random_lots(rng)
    _assign_next_lot(equipment, lots)
    pm_schedule = _pm_schedule(rng, equipment)
    alarms = _random_alarms(rng, equipment, pm_schedule)
    if force_anomaly and force_anomaly in ANOMALY_LABELS and force_anomaly != "none":
        _apply_anomaly(force_anomaly, equipment, alarms)

    bottleneck_load = {
        area: round(float(rng.uniform(0.55, 0.98)), 3)
        for area in ["薄膜", "光刻", "刻蚀", "平坦化"]
    }
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "equipment": equipment,
        "lots": lots,
        "alarms": alarms,
        "pm_schedule": pm_schedule,
        "bottleneck_load": bottleneck_load,
        "wip_total": int(sum(lot["wafer_count"] for lot in lots)),
        "tool_down_count": int(sum(1 for e in equipment if e["status"] == "DOWN")),
        "anomaly": force_anomaly,
    }

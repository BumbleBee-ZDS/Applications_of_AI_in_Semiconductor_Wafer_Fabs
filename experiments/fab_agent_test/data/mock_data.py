"""
data/mock_data.py
==================
FAB 多 Agent 系统的 Mock 数据层。

包含：
1. LOT_DB：批次硬编码数据（基础兜底数据）
2. RECIPE_DB：工艺配方硬编码数据（基础兜底数据）
3. EQUIP_TIMEOUT_RATE：设备接口超时概率（30%）
4. 动态加载 fab_test_data.json（由 DeepSeek 生成）并合并到 DB
5. GENERATED_QUESTIONS：生成的示例问题列表
6. DATA_SOURCE：数据来源标识
"""

import json
from pathlib import Path
from typing import Any, Dict, List


# =====================================================================
# 基础兜底 Mock 数据（当 fab_test_data.json 不存在时仍能运行）
# =====================================================================
LOT_DB: Dict[str, Dict[str, Any]] = {
    "W12345": {
        "lot_id": "W12345",
        "chamber_id": "ETCH-CH-007",
        "product": "LogicChip-A",
        "cd_target_nm": 50.0,
        "cd_measured_nm": 52.8,
        "process_date": "2026-08-09",
        "status": "CD超标",
        "history": "近30天该产品CD超标2次，均关联 ETCH-CH-007 腔体",
    },
    "W67890": {
        "lot_id": "W67890",
        "chamber_id": "ETCH-CH-003",
        "product": "DRAM-B",
        "cd_target_nm": 40.0,
        "cd_measured_nm": 40.5,
        "process_date": "2026-08-08",
        "status": "正常",
        "history": "近30天无异常",
    },
}


RECIPE_DB: Dict[str, Dict[str, Any]] = {
    "W12345": {
        "recipe_id": "RC-2024-ETCH-V3",
        "pressure_setpoint_mtorr": 5.0,
        "rf_power_setpoint_w": 1250,
        "etch_time_sec": 60,
        "gas_flow_sccm": 100,
    },
    "W67890": {
        "recipe_id": "RC-2024-ETCH-V1",
        "pressure_setpoint_mtorr": 4.5,
        "rf_power_setpoint_w": 1200,
        "etch_time_sec": 55,
        "gas_flow_sccm": 95,
    },
}

EQUIP_TIMEOUT_RATE = 0.30  # 设备接口 30% 概率超时


# =====================================================================
# 动态加载 DeepSeek 生成的 fab_test_data.json（若存在）
# =====================================================================
def _load_generated_data() -> List[str]:
    """加载 fab_test_data.json（位于项目根目录或 data/ 目录），合并批次/配方并返回问题列表。"""
    questions: List[str] = []
    candidate_paths: List[Path] = [
        Path(__file__).resolve().parent.parent / "fab_test_data.json",   # 项目根
        Path(__file__).resolve().parent / "fab_test_data.json",         # data/ 目录
        Path("fab_test_data.json"),                                      # 当前工作目录
    ]
    data_path: Path | None = None
    for p in candidate_paths:
        if p.exists():
            data_path = p
            break
    if data_path is None:
        return questions
    try:
        with data_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return questions

    # 合并（生成数据优先，覆盖同 ID 的硬编码数据）
    for lot_id, lot in data.get("lots", {}).items():
        LOT_DB[lot_id] = lot
    for lot_id, recipe in data.get("recipes", {}).items():
        RECIPE_DB[lot_id] = recipe
    questions = [str(q) for q in data.get("questions", [])]
    return questions


GENERATED_QUESTIONS: List[str] = _load_generated_data()
DATA_SOURCE = "DeepSeek 生成" if GENERATED_QUESTIONS else "内置硬编码"


__all__ = [
    "LOT_DB",
    "RECIPE_DB",
    "EQUIP_TIMEOUT_RATE",
    "GENERATED_QUESTIONS",
    "DATA_SOURCE",
]

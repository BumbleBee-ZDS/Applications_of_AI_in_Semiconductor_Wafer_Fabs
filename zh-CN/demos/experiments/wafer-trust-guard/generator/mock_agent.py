"""Generator（模拟 Agent）—— 负责『写代码』：根据自然语言需求生成 Recipe。

背景隐喻：Generator 就像芯片设计中的 RTL 工程师，把需求写成『工艺配方代码』。
它可能『理解错』、『产生幻觉』，所以产出必须交给 Verifier 验证层把关 ——
验证比生成重要。

行为禁令（重要）：
1. 本模块【不得】import 任何 verifier 代码（物理隔离）：
   Generator 只负责生产，不负责也不允许自行裁定对错；
2. 为了 MVP 稳定性，不接真实 LLM API（OpenAI/Claude 等），
   这里用随机逻辑模拟 Agent 行为，并故意以 20% 概率注入『幻觉参数』
   （温度超限 / 漏掉冷却 / 负时间 / 零温度 / 不存在的工艺气体等），
   让演示能直观感受『验证比生成重要』。
"""

import random
import re
from typing import Tuple

COMPLIANT_RATIO = 0.8  # 80% 合规路径，20% 幻觉注入

# 每种幻觉类型的中文描述（面向半导体工程师）
_HALLUCINATION_DESC = {
    "temperature_over": "温度超过 1200°C 物理极限（机台无法承载，流片必失败）",
    "cooling_step_missing": "声明需要冷却却没有冷却时长（漏掉冷却步骤，热应力翘曲风险）",
    "negative_duration": "工艺时长被填成负数（物理上不成立的『负时间』）",
    "zero_temperature": "温度被填成 0°C（零温度自洽性错误）",
    "bad_gas": "幻觉出白名单外的不存在的工艺气体（气体面板无此通道）",
    "cooling_with_zero_duration": "需要冷却但主工艺时长为 0（冷却无意义）",
    "ignores_negation": "需求明确『不要冷却』却被无视（Agent 忽略了否定约束）",
}


def generate_recipe(user_requirement: str) -> dict:
    """生成一个 Recipe（dict 形式）。

    返回的是『流片前的代码』—— 可能包含幻觉参数，必须交给 Verifier 验证。
    """
    recipe, _ = _generate(user_requirement)
    return recipe


def generate_recipe_with_note(user_requirement: str) -> Tuple[dict, str]:
    """生成 Recipe，并附带 Agent 的行为自述（合规 / 幻觉说明），供 UI 展示。"""
    return _generate(user_requirement)


def _generate(user_requirement: str) -> Tuple[dict, str]:
    req = (user_requirement or "").strip()

    # 1) 意图解析（启发式，模拟 Agent 的『理解』）
    step_name = _infer_step(req)
    gas_type = _infer_gas(step_name, req)
    if any(k in req for k in ("不要冷却", "无需冷却", "不需冷却")):
        cooling_required = False  # 尊重否定约束
    else:
        cooling_required = any(k in req for k in ("冷却", "降温")) or random.random() < 0.3
    temp, dur = _typical_parameters(step_name)

    # 2) 参数填充
    recipe = {
        "lot_id": _fake_lot_id(req),
        "step_name": step_name,
        "temperature": temp,
        "duration_sec": dur,
        "cooling_required": cooling_required,
        "gas_type": gas_type,
    }
    if cooling_required:
        recipe["cooling_sec"] = random.choice([120, 180, 240])

    # 3) 幻觉注入（20% 概率）
    if random.random() > COMPLIANT_RATIO:
        kind = _inject_hallucination(recipe, req)
        note = f"⚠️ Agent 本次输出疑似幻觉：{_HALLUCINATION_DESC[kind]} —— 请 Verifier 介入！"
    else:
        note = "✅ Agent 本次输出走正常路径（80% 合规通道），无幻觉注入。"

    return recipe, note


def _inject_hallucination(recipe: dict, req: str) -> str:
    """故意注入一种幻觉参数，返回幻觉类型。"""
    kind = random.choice(list(_HALLUCINATION_DESC))
    # 『无视否定约束』只在需求明确说『不要冷却』时有意义，否则重新抽取
    while kind == "ignores_negation" and not any(
        k in req for k in ("不要冷却", "无需冷却", "不需冷却")
    ):
        kind = random.choice(list(_HALLUCINATION_DESC))
    if kind == "temperature_over":
        recipe["temperature"] = random.choice([1250, 1300, 1350])
    elif kind == "cooling_step_missing":
        recipe["cooling_required"] = True
        recipe["cooling_sec"] = 0
    elif kind == "negative_duration":
        recipe["duration_sec"] = -random.randint(10, 120)
    elif kind == "zero_temperature":
        recipe["temperature"] = 0
    elif kind == "bad_gas":
        recipe["gas_type"] = random.choice(["H2", "CL2", "He"])
    elif kind == "cooling_with_zero_duration":
        recipe["cooling_required"] = True
        recipe["duration_sec"] = 0
    elif kind == "ignores_negation":
        recipe["cooling_required"] = True
    return kind


def _infer_step(req: str) -> str:
    """从需求文本推断工艺类型（模拟 Agent 对需求的理解）。"""
    if any(k in req for k in ("高温", "扩散", "DIFFUSION", "diffusion")):
        return "DIFFUSION"
    if any(k in req for k in ("刻蚀", "蚀刻", "ETCH", "etch")):
        return "ETCH"
    if any(k in req for k in ("清洗", "CLEAN", "clean")):
        return "CLEAN"
    return random.choice(["DIFFUSION", "ETCH", "CLEAN"])


def _infer_gas(step_name: str, req: str) -> str:
    """从需求文本推断工艺气体（模拟 Agent 的常识填充）。"""
    if "O2" in req or "氧气" in req:
        return "O2"
    if "N2" in req or "氮气" in req:
        return "N2"
    if "Ar" in req or "氩气" in req:
        return "Ar"
    if step_name == "CLEAN":
        return random.choice(["O2", "N2"])
    return random.choice(["N2", "Ar"])


def _typical_parameters(step_name: str) -> Tuple[int, int]:
    """给每种工艺一个『看起来正常』的典型参数（模拟 Agent 的领域常识）。"""
    if step_name == "DIFFUSION":
        return random.randint(1050, 1180), random.randint(600, 900)
    if step_name == "ETCH":
        return random.randint(150, 400), random.randint(60, 180)
    return random.randint(60, 120), random.randint(30, 90)


def _fake_lot_id(req: str) -> str:
    """从需求中提取批次号，提取不到则随机生成。"""
    m = re.search(r"(?:批次|lot)\s*([A-Za-z0-9]+)", req, flags=re.IGNORECASE)
    if m:
        return f"LOT-{m.group(1).upper()}"
    return f"LOT-2026-{random.randint(1000, 9999)}"
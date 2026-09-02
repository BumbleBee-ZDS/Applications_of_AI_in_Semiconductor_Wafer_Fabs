"""L2 意图对齐：模拟 LLM-as-Judge，判断 Recipe 是否忠于用户需求。

MVP 阶段用 if-else 规则匹配实现；接口 `judge_alignment(requirement, recipe)`
已预留，后续可无缝替换为真实大模型打分（如接入 DeepSeek / Qwen），
调用方无需改动。
"""

from . import Verdict


def judge_alignment(requirement: str, recipe: dict) -> Verdict:
    """判断 Recipe 是否与用户需求对齐（LLM-Judge 模拟）。

    参数：
        requirement: 用户输入的自然语言工艺需求
        recipe:      Generator 生成的 Recipe（dict）
    返回：
        Verdict
    """
    req = (requirement or "").strip()
    if not req:
        return Verdict(passed=True, reasons=["未提供工艺需求，跳过意图对齐（默认放行）"])

    reasons = []
    ok = True

    # 规则 1：需求提到『高温/扩散』→ step_name 必须是 DIFFUSION
    if any(k in req for k in ("高温", "扩散")):
        if recipe.get("step_name") != "DIFFUSION":
            ok = False
            reasons.append(
                f"需求要求『高温/扩散』工艺，但 Recipe 的 step_name 为 {recipe.get('step_name')}，"
                "应为 DIFFUSION（扩散炉才做高温工艺）"
            )

    # 规则 2：需求提到『清洗』→ gas_type 必须是 O2 或 N2
    if "清洗" in req:
        if recipe.get("gas_type") not in ("O2", "N2"):
            ok = False
            reasons.append(
                f"需求要求『清洗』工艺，但 Recipe 的气体为 {recipe.get('gas_type')}，"
                "清洗腔只能使用 O2 / N2（其余气体无法完成湿法清洗）"
            )

    # 规则 3：需求提到『冷却/降温』（且未明确否定）→ cooling_required 必须为 True
    if not any(k in req for k in ("不要冷却", "无需冷却", "不需冷却")) and any(k in req for k in ("冷却", "降温")):
        if not recipe.get("cooling_required"):
            ok = False
            reasons.append("需求明确要求冷却，但 Recipe 未声明 cooling_required=True（工艺没有降温步骤）")

    # 规则 4：需求明确『不要冷却/无需冷却』→ cooling_required 必须为 False
    if any(k in req for k in ("不要冷却", "无需冷却", "不需冷却")):
        if recipe.get("cooling_required"):
            ok = False
            reasons.append("需求明确要求『不冷却』，但 Recipe 仍声明 cooling_required=True（Agent 忽略了否定约束）")

    if ok:
        return Verdict(passed=True, reasons=["意图对齐通过：Recipe 与用户需求一致（规则匹配模拟 LLM-Judge）"])
    return Verdict(passed=False, reasons=reasons)

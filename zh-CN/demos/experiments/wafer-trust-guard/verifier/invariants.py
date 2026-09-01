"""L3 属性/不变量检查：Recipe 内部自洽性（不依赖外部需求）。

不变量（Invariant）是 Recipe 在任何情况下都必须成立的性质，
例如：总时长必须 > 0、冷却必存在、不允许负时间/零温度等。
"""

from . import Verdict


def check_invariants(recipe: dict) -> Verdict:
    """校验 Recipe 自身的属性不变量，返回 Pass / Fail 及中文原因。"""
    reasons = []
    ok = True

    duration = recipe.get("duration_sec", 0)
    cooling = recipe.get("cooling_sec", 0)
    cooling_req = recipe.get("cooling_required", False)

    # 不变量 1：不允许『负时间』（自洽性）
    if duration < 0:
        ok = False
        reasons.append(f"负时间错误：duration_sec = {duration} 秒，时间为负在物理上不成立")

    # 不变量 2：ETCH 工艺时长不能小于 30 秒
    if recipe.get("step_name") == "ETCH" and duration < 30:
        ok = False
        reasons.append(
            f"ETCH 刻蚀工艺的 duration_sec 不能小于 30 秒（当前 {duration} 秒），"
            "过短会导致刻蚀不完整、整批晶圆报废"
        )

    # 不变量 3：cooling_required == True 时，主工艺时长必须大于 0
    if cooling_req and duration <= 0:
        ok = False
        reasons.append(
            f"冷却不变量：要求冷却但主工艺时长 duration_sec = {duration} 秒，必须大于 0"
        )

    # 不变量 4：『冷却必存在』—— 声明需要冷却，就必须有有效的冷却时长
    if cooling_req and cooling <= 0:
        ok = False
        reasons.append(
            f"冷却必存在：cooling_required=True 但冷却时长 cooling_sec = {cooling} 秒，"
            "缺少冷却步骤会引发热应力翘曲、晶圆开裂"
        )

    # 不变量 5：总时长必须大于 0（主工艺 + 冷却）
    if duration + cooling <= 0:
        ok = False
        reasons.append(
            f"总时长必须大于 0：duration_sec({duration}) + cooling_sec({cooling}) = {duration + cooling} 秒"
        )

    # 不变量 6：不允许『零温度』（自洽性：没有在 0°C 下运行的工艺步骤）
    if recipe.get("temperature") == 0:
        ok = False
        reasons.append("零温度自洽性错误：temperature = 0°C，没有在 0°C 下运行的工艺步骤")

    if ok:
        return Verdict(passed=True, reasons=["全部属性不变量成立：时长为正、冷却存在、温度自洽"])
    return Verdict(passed=False, reasons=reasons)
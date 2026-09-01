"""L1 静态门禁：物理极限 + 格式 + 字段类型（Pydantic 校验）。

对应『流片前的代码审查』：不改业务语义，只查 Recipe 本身是否
符合数据契约与物理常识。
"""

from pydantic import ValidationError

from schemas.recipe import TEMP_MAX, TEMP_MIN, VALID_GASES, VALID_STEPS, WaferRecipe
from . import Verdict


def _pydantic_error_to_chinese(err: dict) -> str:
    """把 Pydantic 的英文错误翻译成半导体工程师可读的中文。"""
    loc = ".".join(str(x) for x in err.get("loc", []))
    typ = err.get("type", "")
    if typ == "missing":
        return f"字段 `{loc}` 缺失（Recipe 不完整，无法编译）"
    if typ in ("int_type", "int_parsing"):
        return f"字段 `{loc}` 类型不合法：应为整数，实际为 {err.get('input')!r}"
    if typ == "string_type":
        return f"字段 `{loc}` 类型不合法：应为字符串，实际为 {err.get('input')!r}"
    if typ == "bool_type":
        return f"字段 `{loc}` 类型不合法：应为布尔值 true/false，实际为 {err.get('input')!r}"
    return f"字段 `{loc}` 校验失败：{err.get('msg', '未知错误')}"


def check_static(recipe_dict: dict) -> Verdict:
    """L1 静态门禁：返回 Pass / Fail 及中文原因。"""
    # 1) 字段类型是否合法（Pydantic 数据契约校验）
    try:
        recipe = WaferRecipe(**recipe_dict)
    except ValidationError as exc:
        reasons = [_pydantic_error_to_chinese(e) for e in exc.errors()]
        return Verdict(passed=False, reasons=reasons)

    # 2) 温度是否在 [TEMP_MIN, TEMP_MAX] 物理区间
    if not (TEMP_MIN <= recipe.temperature <= TEMP_MAX):
        return Verdict(
            passed=False,
            reasons=[
                f"温度超出物理极限 [{TEMP_MIN}, {TEMP_MAX}]°C：当前 {recipe.temperature}°C，"
                "机台无法承载，存在腔体烧毁与整批流片失败风险"
            ],
        )

    # 3) 是否使用了不存在的工艺气体（只允许 N2 / O2 / Ar）
    if recipe.gas_type not in VALID_GASES:
        return Verdict(
            passed=False,
            reasons=[
                f"使用了不存在的工艺气体 '{recipe.gas_type}'（仅允许 {' / '.join(VALID_GASES)}，"
                "气体面板无此通道，接上去就是事故）"
            ],
        )

    # 4) 工艺类型是否在契约枚举内（DIFFUSION / ETCH / CLEAN）
    if recipe.step_name not in VALID_STEPS:
        return Verdict(
            passed=False,
            reasons=[f"工艺类型 '{recipe.step_name}' 不存在（仅允许 {' / '.join(VALID_STEPS)}）"],
        )

    return Verdict(
        passed=True,
        reasons=["静态门禁全部通过：字段类型合法、温度在物理极限内、气体与工艺类型在白名单内"],
    )
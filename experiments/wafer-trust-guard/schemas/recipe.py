"""Wafer Recipe 数据契约（Pydantic 严格定义）。

背景隐喻：工艺配方（Recipe）就是芯片设计代码。
一旦 Recipe 下发到机台，参数错误 = 流片失败 = 巨额损失。
因此这里用 Pydantic 建立严格的、可验证的数据契约，
Verifier 以本契约为『圣经』做静态门禁（L1）。
"""

from pydantic import BaseModel, ConfigDict, Field

# ---- 契约常量（半导体工艺常识）----
# 工艺类型（契约中的 DIFFUSION | ETCH | CLEAN）
VALID_STEPS = ("DIFFUSION", "ETCH", "CLEAN")
# 气体白名单：气体面板只有这三个通道，其余一律视为不存在
VALID_GASES = ("N2", "O2", "Ar")
# 温度物理极限（°C）：超过即超出机台承载能力
TEMP_MIN = 0
TEMP_MAX = 1200


class WaferRecipe(BaseModel):
    """晶圆加工 Recipe 数据契约。

    - 字段类型严格：类型错误直接由 Pydantic 拦截（L1 的『字段类型检查』）；
    - 物理极限（温度区间、气体白名单）由 L1 静态门禁显式校验；
    - cooling_sec 为可选字段（默认 0），用于支撑 L3 的『冷却必存在』不变量。
    """

    model_config = ConfigDict(extra="forbid")  # 禁止多余字段，防止脏数据注入

    lot_id: str = Field(description="批次号，例如 LOT-A 或 LOT-2026-0801")
    step_name: str = Field(description=f"工艺类型，仅允许 {' / '.join(VALID_STEPS)}")
    temperature: int = Field(description=f"工艺温度（°C），物理极限 {TEMP_MIN}~{TEMP_MAX}")
    duration_sec: int = Field(description="主工艺时长（秒），必须为正数")
    gas_type: str = Field(description=f"工艺气体，仅允许 {' / '.join(VALID_GASES)}")
    cooling_required: bool = Field(default=False, description="是否需要冷却步骤")
    cooling_sec: int = Field(
        default=0,
        description="冷却时长（秒）；cooling_required=True 时必须 > 0，用于支撑『冷却必存在』不变量",
    )
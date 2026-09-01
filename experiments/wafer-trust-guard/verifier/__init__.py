"""verifier —— Verifier（验证层）：拥有绝对否决权。

背景隐喻：芯片行业的 Design vs Verification 分离。
Generator 负责『写代码』，Verifier 是唯一能拦住坏 Recipe 的关卡。
本包实现三层拦截：L1 静态门禁 / L2 意图对齐 / L3 属性不变量。
"""

from dataclasses import dataclass, field


@dataclass
class Verdict:
    """一次验证的结果：是否通过（Pass/Fail）+ 中文原因列表。

    - passed=True  ：通过，reasons 为通过说明；
    - passed=False ：不通过，reasons 为面向半导体工程师可读的拦截原因。
    """

    passed: bool
    reasons: list[str] = field(default_factory=list)
"""FabGraph MVP - 晶圆厂数据资产知识图谱系统。

顶层包，对外暴露版本与配置入口。
对应ResNet整体网络：本包为输入特征入口，
下游各子模块逐层提取Schema语义与血缘关系。
"""
from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]

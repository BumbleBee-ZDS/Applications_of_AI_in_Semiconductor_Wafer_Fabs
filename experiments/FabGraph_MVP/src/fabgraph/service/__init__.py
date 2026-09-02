"""服务层 (service)。

业务编排：SQL分析、图谱构建、语义搜索、NL2SQL。
严格依赖 repository 层，不直接写 raw SQL。
对应ResNet残差块：跨层组合特征并注入语义信号。
"""
from __future__ import annotations

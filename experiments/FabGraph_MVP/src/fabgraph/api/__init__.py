"""API层 (api)。

FastAPI 路由聚合层，仅做请求校验与 service 调用，
统一返回结构化 JSON（含错误响应）。
对应ResNet输出层：将深层特征映射为对外结果。
"""
from __future__ import annotations

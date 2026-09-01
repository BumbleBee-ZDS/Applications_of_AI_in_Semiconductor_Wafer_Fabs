"""仓储层 (repository)。

封装所有持久化访问（SQLite元数据 / NetworkX图谱 / FAISS向量），
service 层禁止绕过本层直接操作存储。
对应ResNet池化层：对下层特征做聚合与索引。
"""
from __future__ import annotations

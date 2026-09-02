"""
core/memory.py
================
记忆模块：保存用户提供的批次号（Lot ID），防止 Agent 遗忘。

极简实现：key-value 字典存储。可在后续扩展为持久化 / 向量存储 / 长期记忆。
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Memory:
    _store: Dict[str, Any] = field(default_factory=dict)

    def store(self, key: str, value: Any) -> None:
        self._store[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

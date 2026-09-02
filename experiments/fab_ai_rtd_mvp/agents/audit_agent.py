"""审计 Agent：全链路日志（MVP 用内存实现，生产环境应替换为不可篡改存储）。"""

from __future__ import annotations

import json
from typing import Any, Optional

from utils.helpers import now_iso


class AuditAgent:
    """内存版审计日志：记录每个 Agent 的动作、输入摘要、决策与证据。"""

    def __init__(self) -> None:
        self._logs: list[dict[str, Any]] = []

    def log_event(
        self,
        trace_id: str,
        agent: str,
        action: str,
        input_summary: str,
        decision: str,
        evidence: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """写入一条审计日志。

        Args:
            trace_id: 全链路追踪 ID。
            agent: Agent 名称。
            action: 动作名称。
            input_summary: 输入摘要。
            decision: 决策结果。
            evidence: 结构化证据。
            extra: 附加信息。

        Returns:
            写入的日志记录。
        """
        record = {
            "log_id": f"LOG-{len(self._logs) + 1:04d}",
            "trace_id": trace_id,
            "timestamp": now_iso(),
            "agent": agent,
            "action": action,
            "input_summary": input_summary,
            "decision": decision,
            "evidence": evidence or {},
            "extra": extra or {},
        }
        self._logs.append(record)
        return record

    def get_trace(self, trace_id: str) -> list[dict[str, Any]]:
        """按 trace_id 追溯整条链路的所有日志。"""
        return [log for log in self._logs if log["trace_id"] == trace_id]

    def all_logs(self) -> list[dict[str, Any]]:
        """返回全部日志（副本）。"""
        return list(self._logs)

    def to_json(self) -> str:
        """导出完整审计日志为 JSON 字符串。"""
        return json.dumps(self._logs, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        """清空日志（仅用于演示/测试）。"""
        self._logs.clear()

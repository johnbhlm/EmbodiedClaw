from __future__ import annotations

import time
from typing import Any, Protocol

from apps.openclaw_bridge.progress_formatter import (
    format_dispatch_result,
    format_interpretation_result,
    format_task_summary,
)
from apps.openclaw_bridge.tool_schemas import ToolCallResult


class _ClientLike(Protocol):
    def interpret_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...

    def dispatch_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...

    def get_task_summary(self, task_id: str) -> dict[str, Any]: ...


class EmbodiedClawToolRunner:
    def __init__(self, client: _ClientLike | None = None, base_url: str = 'http://127.0.0.1:8000') -> None:
        if client is not None:
            self.client = client
            return

        from apps.openclaw_tools.embodiedclaw_client import EmbodiedClawClient

        self.client = EmbodiedClawClient(base_url=base_url)

    def interpret_command(self, command: str, context: dict[str, Any] | None = None) -> ToolCallResult:
        result = self.client.interpret_command(command=command, context=context)
        return format_interpretation_result(result)

    def dispatch_command(self, command: str, context: dict[str, Any] | None = None) -> ToolCallResult:
        result = self.client.dispatch_command(command=command, context=context)
        return format_dispatch_result(result)

    def poll_task(self, task_id: str) -> ToolCallResult:
        summary = self.client.get_task_summary(task_id)
        return format_task_summary(summary)

    def run_command_until_terminal(
        self,
        command: str,
        context: dict[str, Any] | None = None,
        poll_interval_sec: float = 1.0,
        max_polls: int = 20,
    ) -> list[ToolCallResult]:
        results: list[ToolCallResult] = []
        dispatch_result = self.dispatch_command(command=command, context=context)
        results.append(dispatch_result)

        if dispatch_result.mode in {'clarification', 'scheduled', 'unsupported', 'failed'}:
            return results

        task_id = dispatch_result.task_id
        if not task_id:
            return results

        for _ in range(max_polls):
            poll_result = self.poll_task(task_id)
            results.append(poll_result)
            if poll_result.mode in {'completed', 'failed'}:
                break
            time.sleep(poll_interval_sec)

        return results

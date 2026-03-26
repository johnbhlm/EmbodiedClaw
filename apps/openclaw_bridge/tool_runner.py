from __future__ import annotations

import time
from typing import Any, Protocol

from apps.openclaw_bridge.openclaw_contract import OpenClawMessageResponse, OpenClawPollResponse
from apps.openclaw_bridge.openclaw_formatter import build_message_response, build_poll_response
from apps.openclaw_bridge.progress_formatter import (
    format_dispatch_result,
    format_interpretation_result,
    format_task_summary,
)
from apps.openclaw_bridge.tool_schemas import ToolCallResult


class _ClientLike(Protocol):
    def interpret_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...

    def dispatch_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...

    def chat_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]: ...

    def get_task_summary(self, task_id: str) -> dict[str, Any]: ...

    def openclaw_poll_task(self, task_id: str) -> dict[str, Any]: ...


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


class OpenClawToolFacade:
    def __init__(self, client: _ClientLike | None = None, base_url: str = 'http://127.0.0.1:8000') -> None:
        self.last_run_trace: list[OpenClawMessageResponse | OpenClawPollResponse] = []
        if client is not None:
            self.client = client
            return

        from apps.openclaw_tools.embodiedclaw_client import EmbodiedClawClient

        self.client = EmbodiedClawClient(base_url=base_url)

    def handle_message(self, command: str, context: dict[str, Any] | None = None) -> OpenClawMessageResponse:
        chat_result = self.client.chat_command(command=command, context=context)
        return build_message_response(chat_result)

    def poll_task(self, task_id: str) -> OpenClawPollResponse:
        if hasattr(self.client, 'openclaw_poll_task'):
            return build_poll_response(self.client.openclaw_poll_task(task_id))
        summary = self.client.get_task_summary(task_id)
        return build_poll_response(summary)

    def run_until_terminal(
        self,
        command: str,
        context: dict[str, Any] | None = None,
        poll_interval_sec: float = 1.0,
        max_polls: int = 20,
    ) -> list[str]:
        first = self.handle_message(command=command, context=context)
        self.last_run_trace = [first]
        messages = [first.reply_text]

        if not first.needs_polling or not first.task_id:
            return messages

        last_message = first.reply_text
        for _ in range(max_polls):
            polled = self.poll_task(first.task_id)
            self.last_run_trace.append(polled)
            if polled.reply_text != last_message:
                messages.append(polled.reply_text)
                last_message = polled.reply_text
            if polled.terminal:
                break
            time.sleep(poll_interval_sec)

        return messages

from __future__ import annotations

from typing import Any, Callable

from apps.reasoning.schemas import InterpretationResult


def build_dispatch_response(
    interpretation: InterpretationResult,
    submit_task_func: Callable[[str, dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    response: dict[str, Any] = {'interpretation': interpretation.to_dict()}
    if interpretation.status == 'executable':
        task_spec = interpretation.task_spec or {}
        task_type = task_spec.get('task_type')
        task_payload = task_spec.get('task_payload', {})
        if not isinstance(task_type, str):
            raise ValueError('Interpreter produced invalid task_spec')
        response['task_submission'] = submit_task_func(task_type, task_payload)
    return response

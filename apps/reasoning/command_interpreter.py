from __future__ import annotations

from typing import Any

from apps.reasoning.clarification import (
    clarify_missing_recipient_location,
    clarify_missing_surface,
    unsupported_command_reason,
)
from apps.reasoning.normalization import normalize_command_text
from apps.reasoning.schemas import InterpretationResult


class CommandInterpreter:
    """Deterministic demo command interpreter for M3-beta."""

    def interpret(self, command: str, context: dict[str, Any] | None = None) -> InterpretationResult:
        normalized = normalize_command_text(command)
        runtime_context = context or {}

        if normalized == '往前走一米':
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={'task_type': 'move_forward', 'task_payload': {'distance_m': 1.0}},
            )

        if normalized == '左转45度':
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={'task_type': 'rotate_relative', 'task_payload': {'yaw_deg': 45}},
            )

        if normalized == '右转45度':
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={'task_type': 'rotate_relative', 'task_payload': {'yaw_deg': -45}},
            )

        if normalized == '你看到了什么':
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={'task_type': 'observe_scene', 'task_payload': {'area': 'current_view'}},
            )

        if normalized == '桌子上都有什么':
            surface_id = runtime_context.get('surface_id')
            clarification = clarify_missing_surface(surface_id, 'list_objects_on_surface')
            if clarification.needs_clarification:
                return InterpretationResult(
                    status='clarification_needed',
                    normalized_command=normalized,
                    clarification_question=clarification.question,
                    reason=clarification.reason,
                )
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={'task_type': 'list_objects_on_surface', 'task_payload': {'surface_id': surface_id}},
            )

        if normalized == '收拾一下桌子':
            area = runtime_context.get('area') or runtime_context.get('surface_id')
            clarification = clarify_missing_surface(area, 'tidy_desk')
            if clarification.needs_clarification:
                return InterpretationResult(
                    status='clarification_needed',
                    normalized_command=normalized,
                    clarification_question=clarification.question,
                    reason=clarification.reason,
                )
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={'task_type': 'tidy_desk', 'task_payload': {'area': area}},
            )

        if normalized == '将餐桌上苹果给我':
            recipient_location = runtime_context.get('recipient_location')
            clarification = clarify_missing_recipient_location(recipient_location)
            if clarification.needs_clarification:
                return InterpretationResult(
                    status='clarification_needed',
                    normalized_command=normalized,
                    clarification_question=clarification.question,
                    reason=clarification.reason,
                    task_spec={
                        'task_type': 'bring_object',
                        'task_payload': {
                            'object_name': 'apple',
                            'source_location': 'dining_table',
                            'recipient_location': None,
                        },
                    },
                )
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={
                    'task_type': 'bring_object',
                    'task_payload': {
                        'object_name': 'apple',
                        'source_location': 'dining_table',
                        'recipient_location': recipient_location,
                    },
                },
            )

        if normalized == '每天晚上九点巡检窗户和灯是否关闭':
            return InterpretationResult(
                status='scheduled_task',
                normalized_command=normalized,
                task_spec={'task_type': 'inspect_windows_and_lights', 'task_payload': {}},
                schedule={'type': 'daily', 'time': '21:00'},
            )

        if normalized in {'停止', '终止任务', '别动了'}:
            return InterpretationResult(
                status='executable',
                normalized_command=normalized,
                task_spec={'task_type': 'stop_task', 'task_payload': {}},
            )

        return InterpretationResult(
            status='unsupported',
            normalized_command=normalized,
            reason=unsupported_command_reason(normalized),
        )

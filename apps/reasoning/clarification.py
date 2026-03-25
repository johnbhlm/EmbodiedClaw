from __future__ import annotations

from apps.reasoning.schemas import ClarificationResult


def clarify_missing_recipient_location(recipient_location: str | None) -> ClarificationResult:
    if recipient_location:
        return ClarificationResult(needs_clarification=False)
    return ClarificationResult(
        needs_clarification=True,
        question='请问你现在在哪里？或者我先观察并定位你的位置？',
        reason='bring_object requires recipient_location',
    )


def clarify_missing_surface(surface_id: str | None, task_type: str) -> ClarificationResult:
    if surface_id:
        return ClarificationResult(needs_clarification=False)

    if task_type == 'list_objects_on_surface':
        question = '你想让我查看哪一张桌子或台面？'
    else:
        question = '你想让我整理哪一张桌子或台面？'

    return ClarificationResult(
        needs_clarification=True,
        question=question,
        reason=f'{task_type} requires target surface/area',
    )


def unsupported_command_reason(normalized_command: str) -> str:
    return f'Unsupported command for M3-beta demo contract: {normalized_command}'

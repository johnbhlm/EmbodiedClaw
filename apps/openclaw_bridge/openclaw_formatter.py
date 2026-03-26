from __future__ import annotations

from apps.openclaw_bridge.openclaw_contract import OpenClawMessageResponse, OpenClawPollResponse


def _normalize_image_uris(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _extract_image_uris(task_summary: dict) -> list[str]:
    result = task_summary.get('result') if isinstance(task_summary, dict) else None
    if not isinstance(result, dict):
        result = {}

    artifact_uris = _normalize_image_uris(result.get('artifact_uris'))
    if artifact_uris:
        return artifact_uris

    explicit_candidates = [
        _normalize_image_uris(result.get('image_uris')),
        _normalize_image_uris(task_summary.get('image_uris')),
    ]
    for candidate in explicit_candidates:
        if candidate:
            return candidate

    primary_candidates = [
        result.get('primary_image_uri'),
        task_summary.get('primary_image_uri'),
        task_summary.get('latest_image_uri'),
    ]
    for candidate in primary_candidates:
        if isinstance(candidate, str) and candidate.strip():
            return [candidate]

    return []


def build_message_response(chat_result: dict) -> OpenClawMessageResponse:
    interpretation = chat_result.get('interpretation') or {}
    status = interpretation.get('status')
    task_id = chat_result.get('task_id')

    if status == 'clarification_needed':
        question = interpretation.get('clarification_question') or '请补充更多上下文。'
        return OpenClawMessageResponse(
            ok=True,
            mode='clarification',
            reply_text=f'我还需要一些信息：{question}',
            task_id=None,
            needs_polling=False,
            terminal=True,
            raw=chat_result,
        )

    if status == 'scheduled_task':
        return OpenClawMessageResponse(
            ok=True,
            mode='scheduled',
            reply_text='已识别为计划任务，但当前还未自动启用调度执行，请确认后再下发。',
            task_id=None,
            needs_polling=False,
            terminal=True,
            raw=chat_result,
        )

    if status == 'unsupported':
        return OpenClawMessageResponse(
            ok=True,
            mode='unsupported',
            reply_text='当前还不支持这个指令，请换一种说法或补充结构化信息。',
            task_id=None,
            needs_polling=False,
            terminal=True,
            raw=chat_result,
        )

    # executable / submitted
    return OpenClawMessageResponse(
        ok=bool(task_id),
        mode='submitted',
        reply_text='已开始执行任务，我会持续反馈进度。' if task_id else '任务提交失败，暂时无法开始执行。',
        task_id=task_id,
        needs_polling=bool(task_id),
        terminal=not bool(task_id),
        raw=chat_result,
    )


def build_poll_response(task_summary: dict) -> OpenClawPollResponse:
    status = (task_summary.get('final_status') or '').upper()
    task_id = task_summary.get('task_id')
    progress = task_summary.get('progress')
    image_uris = _extract_image_uris(task_summary)
    primary_image_uri = image_uris[0] if image_uris else None

    if status in {'RUNNING', 'ACCEPTED', 'CREATED'}:
        latest_stage = task_summary.get('latest_stage') or 'UNKNOWN'
        latest_message = task_summary.get('latest_message') or '暂无详细反馈'
        return OpenClawPollResponse(
            ok=True,
            mode='running',
            reply_text=f'正在执行：{latest_stage}，{latest_message}',
            task_id=task_id,
            terminal=False,
            progress=progress,
            image_uris=[],
            primary_image_uri=None,
            raw=task_summary,
        )

    if status == 'SUCCEEDED':
        result = task_summary.get('result') or {}
        summary = result.get('summary') or str(result) or '任务执行完成'
        task_type = (task_summary.get('task_type') or '').lower()
        observe_like = (
            bool(image_uris)
            or task_type in {'observe_scene', 'list_objects_on_surface', 'inspect_windows', 'inspect_windows_and_lights'}
        )
        if observe_like and image_uris:
            reply_text = '任务已完成，已获取当前画面。'
        elif observe_like:
            reply_text = f'任务已完成：{summary}'
        else:
            reply_text = f'任务已完成：{summary}'
        return OpenClawPollResponse(
            ok=True,
            mode='completed',
            reply_text=reply_text,
            task_id=task_id,
            terminal=True,
            progress=progress if progress is not None else 1.0,
            image_uris=image_uris,
            primary_image_uri=primary_image_uri,
            raw=task_summary,
        )

    if status in {'FAILED', 'FAILED_TO_SUBMIT', 'REJECTED'}:
        result = task_summary.get('result') or {}
        reason = result.get('summary') or result.get('error_code') or task_summary.get('latest_message') or status
        return OpenClawPollResponse(
            ok=False,
            mode='failed',
            reply_text=f'任务失败：{reason}',
            task_id=task_id,
            terminal=True,
            progress=progress,
            image_uris=image_uris,
            primary_image_uri=primary_image_uri,
            raw=task_summary,
        )

    return OpenClawPollResponse(
        ok=False,
        mode='unknown',
        reply_text='暂时无法获取任务状态',
        task_id=task_id,
        terminal=True,
        progress=progress,
        image_uris=[],
        primary_image_uri=None,
        raw=task_summary,
    )

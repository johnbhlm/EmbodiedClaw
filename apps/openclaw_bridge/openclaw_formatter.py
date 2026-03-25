from __future__ import annotations

from apps.openclaw_bridge.openclaw_contract import OpenClawMessageResponse, OpenClawPollResponse


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
            raw=task_summary,
        )

    if status == 'SUCCEEDED':
        result = task_summary.get('result') or {}
        summary = result.get('summary') or str(result) or '任务执行完成'
        return OpenClawPollResponse(
            ok=True,
            mode='completed',
            reply_text=f'任务已完成：{summary}',
            task_id=task_id,
            terminal=True,
            progress=progress if progress is not None else 1.0,
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
            raw=task_summary,
        )

    return OpenClawPollResponse(
        ok=False,
        mode='unknown',
        reply_text='暂时无法获取任务状态',
        task_id=task_id,
        terminal=True,
        progress=progress,
        raw=task_summary,
    )

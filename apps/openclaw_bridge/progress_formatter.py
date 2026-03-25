from __future__ import annotations

from typing import Any

from apps.openclaw_bridge.tool_schemas import ToolCallResult


def format_interpretation_result(result: dict[str, Any]) -> ToolCallResult:
    status = str(result.get('status', 'unsupported'))
    if status == 'clarification_needed':
        question = result.get('clarification_question') or '请补充更多信息，便于我准确执行。'
        return ToolCallResult(
            ok=True,
            mode='clarification',
            message=f'需要澄清：{question}',
            raw=result,
        )

    if status == 'scheduled_task':
        return ToolCallResult(
            ok=True,
            mode='scheduled',
            message='已识别为定时任务，调度解析成功；当前版本尚未自动启用调度执行。',
            raw=result,
        )

    if status == 'unsupported':
        reason = result.get('reason') or '当前命令不在支持范围内。'
        return ToolCallResult(ok=False, mode='unsupported', message=f'暂不支持该命令：{reason}', raw=result)

    if status == 'executable':
        return ToolCallResult(ok=True, mode='submitted', message='命令可执行，可发起任务。', raw=result)

    return ToolCallResult(ok=False, mode='failed', message=f'未知解释状态：{status}', raw=result)


def format_dispatch_result(result: dict[str, Any]) -> ToolCallResult:
    interpretation = result.get('interpretation') or {}
    interpreted = format_interpretation_result(interpretation)
    if interpreted.mode in {'clarification', 'scheduled', 'unsupported'}:
        return ToolCallResult(
            ok=interpreted.ok,
            mode=interpreted.mode,
            message=interpreted.message,
            task_id=None,
            raw=result,
        )

    task_submission = result.get('task_submission') or {}
    task_id = task_submission.get('task_id')
    if isinstance(task_id, str) and task_id:
        return ToolCallResult(
            ok=True,
            mode='submitted',
            message=f'任务已提交，task_id={task_id}',
            task_id=task_id,
            raw=result,
        )

    return ToolCallResult(ok=False, mode='failed', message='任务提交失败：缺少 task_id', raw=result)


def format_task_summary(summary: dict[str, Any]) -> ToolCallResult:
    final_status = str(summary.get('final_status') or '')
    task_id = summary.get('task_id')
    stage = summary.get('latest_stage') or 'UNKNOWN'
    latest_message = summary.get('latest_message') or ''
    progress = float(summary.get('progress') or 0.0)

    if final_status in {'SUCCEEDED', 'COMPLETED'}:
        result = summary.get('result') or {}
        result_summary = result.get('summary') or '任务已完成。'
        return ToolCallResult(
            ok=True,
            mode='completed',
            message=f'任务完成：{result_summary}',
            task_id=task_id,
            raw=summary,
        )

    if final_status in {'FAILED', 'FAILED_TO_SUBMIT', 'REJECTED'}:
        result = summary.get('result') or {}
        reason = result.get('summary') or summary.get('latest_status') or '未知错误'
        return ToolCallResult(
            ok=False,
            mode='failed',
            message=f'任务失败：{reason}',
            task_id=task_id,
            raw=summary,
        )

    display_progress = int(progress * 100)
    message_suffix = f'，{latest_message}' if latest_message else ''
    return ToolCallResult(
        ok=True,
        mode='running',
        message=f'任务执行中：阶段={stage}，进度={display_progress}%{message_suffix}',
        task_id=task_id,
        raw=summary,
    )

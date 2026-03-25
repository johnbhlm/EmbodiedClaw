import unittest

from apps.openclaw_bridge.progress_formatter import (
    format_dispatch_result,
    format_interpretation_result,
    format_task_summary,
)


class ProgressFormatterTests(unittest.TestCase):
    def test_clarification_formatting(self) -> None:
        result = format_interpretation_result(
            {
                'status': 'clarification_needed',
                'clarification_question': '请问目的地是哪里？',
            }
        )
        self.assertEqual('clarification', result.mode)
        self.assertIn('需要澄清', result.message)

    def test_scheduled_formatting(self) -> None:
        result = format_interpretation_result({'status': 'scheduled_task'})
        self.assertEqual('scheduled', result.mode)
        self.assertIn('尚未自动启用调度执行', result.message)

    def test_running_task_formatting(self) -> None:
        result = format_task_summary(
            {
                'task_id': 't1',
                'final_status': 'RUNNING',
                'latest_stage': 'NAVIGATING',
                'latest_message': '正在前往目标',
                'progress': 0.5,
            }
        )
        self.assertEqual('running', result.mode)
        self.assertIn('NAVIGATING', result.message)

    def test_completed_task_formatting(self) -> None:
        result = format_task_summary(
            {
                'task_id': 't1',
                'final_status': 'SUCCEEDED',
                'result': {'summary': '任务执行成功'},
            }
        )
        self.assertEqual('completed', result.mode)
        self.assertIn('任务执行成功', result.message)

    def test_failed_task_formatting(self) -> None:
        result = format_task_summary(
            {
                'task_id': 't1',
                'final_status': 'FAILED',
                'result': {'summary': '导航失败'},
            }
        )
        self.assertEqual('failed', result.mode)
        self.assertIn('导航失败', result.message)

    def test_dispatch_submission_formatting(self) -> None:
        result = format_dispatch_result(
            {
                'interpretation': {'status': 'executable'},
                'task_submission': {'task_id': 'abc-123'},
            }
        )
        self.assertEqual('submitted', result.mode)
        self.assertEqual('abc-123', result.task_id)


if __name__ == '__main__':
    unittest.main()

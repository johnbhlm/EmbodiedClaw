import unittest

from apps.openclaw_bridge.openclaw_formatter import build_message_response, build_poll_response


class OpenClawFormatterTests(unittest.TestCase):
    def test_clarification_message_response(self) -> None:
        response = build_message_response(
            {
                'interpretation': {
                    'status': 'clarification_needed',
                    'clarification_question': '请问是哪个房间？',
                },
                'task_id': None,
            }
        )
        self.assertEqual('clarification', response.mode)
        self.assertTrue(response.terminal)
        self.assertFalse(response.needs_polling)

    def test_scheduled_message_response(self) -> None:
        response = build_message_response({'interpretation': {'status': 'scheduled_task'}, 'task_id': None})
        self.assertEqual('scheduled', response.mode)
        self.assertTrue(response.terminal)
        self.assertFalse(response.needs_polling)

    def test_submitted_message_response(self) -> None:
        response = build_message_response({'interpretation': {'status': 'executable'}, 'task_id': 'task-1'})
        self.assertEqual('submitted', response.mode)
        self.assertTrue(response.needs_polling)
        self.assertFalse(response.terminal)

    def test_running_poll_response(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-1',
                'final_status': 'RUNNING',
                'latest_stage': 'NAVIGATING',
                'latest_message': '正在前往目标',
                'progress': 0.5,
            }
        )
        self.assertEqual('running', response.mode)
        self.assertFalse(response.terminal)

    def test_completed_poll_response(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-1',
                'final_status': 'SUCCEEDED',
                'result': {'summary': '已完成巡检'},
                'progress': 1.0,
            }
        )
        self.assertEqual('completed', response.mode)
        self.assertTrue(response.terminal)

    def test_failed_poll_response(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-1',
                'final_status': 'FAILED',
                'result': {'summary': '导航异常'},
                'progress': 0.7,
            }
        )
        self.assertEqual('failed', response.mode)
        self.assertTrue(response.terminal)


if __name__ == '__main__':
    unittest.main()

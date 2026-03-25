import unittest

from apps.openclaw_bridge.tool_runner import OpenClawToolFacade


class StubOpenClawClient:
    def __init__(self) -> None:
        self.chat_calls = []
        self.summary_calls = []
        self.summaries = [
            {
                'task_id': 'task-1',
                'final_status': 'RUNNING',
                'latest_stage': 'NAVIGATING',
                'latest_message': '移动中',
                'progress': 0.5,
            },
            {
                'task_id': 'task-1',
                'final_status': 'SUCCEEDED',
                'result': {'summary': '执行完成'},
                'progress': 1.0,
            },
        ]

    def chat_command(self, command, context=None):
        self.chat_calls.append((command, context))
        return {'interpretation': {'status': 'executable'}, 'task_id': 'task-1'}

    def get_task_summary(self, task_id):
        self.summary_calls.append(task_id)
        return self.summaries.pop(0)


class OpenClawFacadeTests(unittest.TestCase):
    def test_handle_message_maps_to_submitted(self) -> None:
        facade = OpenClawToolFacade(client=StubOpenClawClient())
        response = facade.handle_message('往前走一米')
        self.assertEqual('submitted', response.mode)
        self.assertTrue(response.needs_polling)
        self.assertEqual('task-1', response.task_id)

    def test_poll_task_maps_running_then_completed(self) -> None:
        client = StubOpenClawClient()
        facade = OpenClawToolFacade(client=client)

        first = facade.poll_task('task-1')
        second = facade.poll_task('task-1')

        self.assertEqual('running', first.mode)
        self.assertEqual('completed', second.mode)

    def test_run_until_terminal_returns_user_messages(self) -> None:
        facade = OpenClawToolFacade(client=StubOpenClawClient())
        messages = facade.run_until_terminal('往前走一米', poll_interval_sec=0.0, max_polls=5)
        self.assertGreaterEqual(len(messages), 2)
        self.assertIn('已开始执行任务', messages[0])
        self.assertIn('任务已完成', messages[-1])


if __name__ == '__main__':
    unittest.main()

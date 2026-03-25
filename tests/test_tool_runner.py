import unittest

from apps.openclaw_bridge.tool_runner import EmbodiedClawToolRunner


class StubClient:
    def __init__(self, dispatch_payload, summaries):
        self.dispatch_payload = dispatch_payload
        self.summaries = list(summaries)
        self.interpret_calls = []
        self.dispatch_calls = []
        self.summary_calls = []

    def interpret_command(self, command, context=None):
        self.interpret_calls.append((command, context))
        return {'status': 'executable'}

    def dispatch_command(self, command, context=None):
        self.dispatch_calls.append((command, context))
        return self.dispatch_payload

    def get_task_summary(self, task_id):
        self.summary_calls.append(task_id)
        if self.summaries:
            return self.summaries.pop(0)
        return {'task_id': task_id, 'final_status': 'RUNNING', 'latest_stage': 'WAITING', 'progress': 0.0}


class ToolRunnerTests(unittest.TestCase):
    def test_interpret_command(self) -> None:
        runner = EmbodiedClawToolRunner(client=StubClient({}, []))
        result = runner.interpret_command('往前走一米')
        self.assertEqual('submitted', result.mode)

    def test_run_returns_immediately_for_clarification(self) -> None:
        client = StubClient({'interpretation': {'status': 'clarification_needed', 'clarification_question': '补充信息？'}}, [])
        runner = EmbodiedClawToolRunner(client=client)

        results = runner.run_command_until_terminal('将餐桌上苹果给我', max_polls=3)

        self.assertEqual(1, len(results))
        self.assertEqual('clarification', results[0].mode)
        self.assertEqual([], client.summary_calls)

    def test_run_polls_until_completed(self) -> None:
        client = StubClient(
            {'interpretation': {'status': 'executable'}, 'task_submission': {'task_id': 't-123'}},
            [
                {
                    'task_id': 't-123',
                    'final_status': 'RUNNING',
                    'latest_stage': 'NAVIGATING',
                    'latest_message': 'moving',
                    'progress': 0.4,
                },
                {
                    'task_id': 't-123',
                    'final_status': 'SUCCEEDED',
                    'result': {'summary': 'ok'},
                    'progress': 1.0,
                },
            ],
        )
        runner = EmbodiedClawToolRunner(client=client)

        results = runner.run_command_until_terminal('往前走一米', poll_interval_sec=0.0, max_polls=5)

        self.assertEqual('submitted', results[0].mode)
        self.assertEqual('running', results[1].mode)
        self.assertEqual('completed', results[2].mode)
        self.assertEqual(2, len(client.summary_calls))


if __name__ == '__main__':
    unittest.main()

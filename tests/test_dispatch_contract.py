import unittest

from apps.reasoning.dispatch_contract import build_dispatch_response
from apps.reasoning.schemas import InterpretationResult


class DispatchContractTests(unittest.TestCase):
    def test_executable_dispatch_submits_task(self) -> None:
        interpretation = InterpretationResult(
            status='executable',
            normalized_command='往前走一米',
            task_spec={'task_type': 'move_forward', 'task_payload': {'distance_m': 1.0}},
        )

        calls = []

        def submit(task_type: str, task_payload: dict) -> dict:
            calls.append((task_type, task_payload))
            return {'task_id': 't1'}

        response = build_dispatch_response(interpretation, submit)
        self.assertEqual(1, len(calls))
        self.assertEqual('move_forward', calls[0][0])
        self.assertEqual({'task_id': 't1'}, response['task_submission'])

    def test_non_executable_does_not_submit(self) -> None:
        interpretation = InterpretationResult(
            status='clarification_needed',
            normalized_command='将餐桌上苹果给我',
            clarification_question='请问你现在在哪里？或者我先观察并定位你的位置？',
            reason='bring_object requires recipient_location',
        )

        def submit(_: str, __: dict) -> dict:
            raise AssertionError('submit must not be called')

        response = build_dispatch_response(interpretation, submit)
        self.assertIn('interpretation', response)
        self.assertNotIn('task_submission', response)


if __name__ == '__main__':
    unittest.main()

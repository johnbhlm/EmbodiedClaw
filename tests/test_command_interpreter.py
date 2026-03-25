import unittest

from apps.reasoning.command_interpreter import CommandInterpreter


class CommandInterpreterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.interpreter = CommandInterpreter()

    def test_move_forward_command(self) -> None:
        result = self.interpreter.interpret('往前走一米')
        self.assertEqual('executable', result.status)
        self.assertEqual('move_forward', result.task_spec['task_type'])
        self.assertEqual(1.0, result.task_spec['task_payload']['distance_m'])

    def test_rotate_command(self) -> None:
        result = self.interpreter.interpret('左转45度')
        self.assertEqual('rotate_relative', result.task_spec['task_type'])

    def test_observe_command(self) -> None:
        result = self.interpreter.interpret('你看到了什么')
        self.assertEqual('observe_scene', result.task_spec['task_type'])

    def test_list_objects_without_context_needs_clarification(self) -> None:
        result = self.interpreter.interpret('桌子上都有什么')
        self.assertEqual('clarification_needed', result.status)

    def test_tidy_desk_without_target_needs_clarification(self) -> None:
        result = self.interpreter.interpret('收拾一下桌子')
        self.assertEqual('clarification_needed', result.status)

        with_context = self.interpreter.interpret('收拾一下桌子', {'area': 'desk_01'})
        self.assertEqual('executable', with_context.status)
        self.assertEqual('tidy_desk', with_context.task_spec['task_type'])

    def test_bring_object_needs_recipient_location(self) -> None:
        result = self.interpreter.interpret('将餐桌上苹果给我')
        self.assertEqual('clarification_needed', result.status)

    def test_scheduled_inspection_command(self) -> None:
        result = self.interpreter.interpret('每天晚上九点巡检窗户和灯是否关闭')
        self.assertEqual('scheduled_task', result.status)
        self.assertEqual('inspect_windows_and_lights', result.task_spec['task_type'])
        self.assertEqual('21:00', result.schedule['time'])

    def test_stop_command(self) -> None:
        result = self.interpreter.interpret('停止')
        self.assertEqual('stop_task', result.task_spec['task_type'])


if __name__ == '__main__':
    unittest.main()

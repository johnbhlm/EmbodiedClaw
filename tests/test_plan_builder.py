import unittest

from apps.tasking.plan_builder import PlanBuilder
from apps.tasking.skill_vocab import CanonicalSkill, TaskType
from apps.tasking.task_protocol import TaskSpec


class PlanBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = PlanBuilder()

    def test_move_forward_builds_one_step(self) -> None:
        plan = self.builder.build(
            TaskSpec(task_id='t1', task_type=TaskType.MOVE_FORWARD, task_payload={'distance_m': 1.0})
        )
        self.assertEqual(1, len(plan))
        self.assertEqual(CanonicalSkill.MOVE_FORWARD, plan[0].skill_name)

    def test_rotate_relative_maps_to_navigate_to(self) -> None:
        plan = self.builder.build(
            TaskSpec(task_id='t2', task_type=TaskType.ROTATE_RELATIVE, task_payload={'yaw_deg': 45})
        )
        self.assertEqual(CanonicalSkill.NAVIGATE_TO, plan[0].skill_name)
        self.assertEqual(45.0, plan[0].params['relative_pose']['yaw_deg'])

    def test_bring_object_contains_observe_pick_place(self) -> None:
        plan = self.builder.build(
            TaskSpec(
                task_id='t3',
                task_type=TaskType.BRING_OBJECT,
                task_payload={
                    'object_name': 'apple',
                    'source_location': 'dining_table',
                    'recipient_location': 'user_location',
                },
            )
        )
        skills = [step.skill_name for step in plan]
        self.assertIn(CanonicalSkill.OBSERVE, skills)
        self.assertIn(CanonicalSkill.PICK, skills)
        self.assertIn(CanonicalSkill.PLACE_INTO, skills)

    def test_inspect_windows_and_lights_expands_targets(self) -> None:
        plan = self.builder.build(
            TaskSpec(
                task_id='t4',
                task_type=TaskType.INSPECT_WINDOWS_AND_LIGHTS,
                task_payload={
                    'window_targets': ['window_01', 'window_02'],
                    'light_targets': ['light_01'],
                },
            )
        )
        self.assertEqual(6, len(plan))
        self.assertEqual(CanonicalSkill.NAVIGATE_TO, plan[0].skill_name)
        self.assertEqual(CanonicalSkill.OBSERVE, plan[1].skill_name)


if __name__ == '__main__':
    unittest.main()

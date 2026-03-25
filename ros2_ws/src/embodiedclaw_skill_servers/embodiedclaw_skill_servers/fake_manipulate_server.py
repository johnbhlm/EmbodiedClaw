import json
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import ManipulateSkill

SUPPORTED_MANIP_SKILLS = {'pick', 'place_into', 'open', 'close', 'toggle', 'tidy_surface'}


class FakeManipulateSkillServer(Node):
    def __init__(self) -> None:
        super().__init__('fake_manipulate_skill_server')
        self._action_server = ActionServer(
            self,
            ManipulateSkill,
            '/assistant/manipulate_skill',
            execute_callback=self.execute_callback,
        )
        self.get_logger().info('Fake manipulate skill server ready.')

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        self.get_logger().info(
            f'Manipulate request_id={goal.request_id} skill_name={goal.skill_name} '
            f'target_object={goal.target_object} target_place={goal.target_place}'
        )

        skill_name = goal.skill_name or 'unknown'
        if skill_name not in SUPPORTED_MANIP_SKILLS:
            goal_handle.abort()
            result = ManipulateSkill.Result()
            result.success = False
            result.detail = f'Unsupported manipulate skill_name={skill_name}'
            result.artifact_uris = []
            return result

        for phase, progress, message, image_uri in [
            ('STARTED', 0.2, f'{skill_name} request accepted', ''),
            ('EXECUTING', 0.65, f'Executing {skill_name}', f'mock://images/{skill_name}_step.jpg'),
            ('FINALIZING', 0.95, f'Finalizing {skill_name}', f'mock://images/{skill_name}_done.jpg'),
        ]:
            feedback = ManipulateSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            feedback.image_uri = image_uri
            goal_handle.publish_feedback(feedback)
            time.sleep(0.2)

        try:
            params = json.loads(goal.params_json) if goal.params_json else {}
        except json.JSONDecodeError:
            params = {}

        goal_handle.succeed()
        result = ManipulateSkill.Result()
        result.success = True
        result.detail = f'{skill_name} completed for {goal.target_object or goal.target_place or "target"}'
        result.artifact_uris = [
            f'mock://artifacts/{skill_name}_before.jpg',
            f'mock://artifacts/{skill_name}_after.jpg',
        ]
        if params.get('target'):
            result.artifact_uris.append(f"mock://artifacts/{skill_name}_{params['target']}.json")
        return result


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FakeManipulateSkillServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

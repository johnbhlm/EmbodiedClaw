import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import ManipulateSkill


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

        stages = [
            ('STARTED', 0.15, 'Manipulation request accepted', ''),
            ('LOCATING_OBJECTS', 0.4, 'Locating clutter on surface', ''),
            ('REARRANGING', 0.75, 'Tidying and grouping items', 'mock://images/tidy_step_1.jpg'),
            ('FINALIZING', 0.95, 'Final touches on target area', 'mock://images/tidy_step_2.jpg'),
        ]

        for phase, progress, message, image_uri in stages:
            feedback = ManipulateSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            feedback.image_uri = image_uri
            goal_handle.publish_feedback(feedback)
            time.sleep(0.3)

        goal_handle.succeed()
        result = ManipulateSkill.Result()
        result.success = True
        result.detail = f'Tidy simulation complete using skill {goal.skill_name or "unknown"}'
        result.artifact_uris = [
            'mock://artifacts/tidy_before.jpg',
            'mock://artifacts/tidy_after.jpg',
        ]
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

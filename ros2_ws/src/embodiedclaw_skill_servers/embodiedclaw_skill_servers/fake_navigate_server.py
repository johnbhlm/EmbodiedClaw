import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import NavigateSkill


class FakeNavigateSkillServer(Node):
    def __init__(self) -> None:
        super().__init__('fake_navigate_skill_server')
        self._action_server = ActionServer(
            self,
            NavigateSkill,
            '/assistant/navigate_skill',
            execute_callback=self.execute_callback,
        )
        self.get_logger().info('Fake navigate skill server ready.')

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        self.get_logger().info(
            f'Navigate request_id={goal.request_id} target_type={goal.target_type} '
            f'location_id={goal.location_id}'
        )

        for phase, progress, message in [
            ('STARTED', 0.2, 'Navigation request accepted'),
            ('MOVING', 0.6, 'Moving toward target location'),
            ('APPROACHING', 0.95, 'Approaching final pose'),
        ]:
            feedback = NavigateSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            goal_handle.publish_feedback(feedback)
            time.sleep(0.25)

        goal_handle.succeed()
        result = NavigateSkill.Result()
        result.success = True
        result.detail = f'Arrived at {goal.location_id or "target"}'
        return result


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FakeNavigateSkillServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

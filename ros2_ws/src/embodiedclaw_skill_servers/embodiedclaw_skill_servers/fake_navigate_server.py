import json
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
            f'location_id={goal.location_id} pose_json={goal.pose_json}'
        )

        pose_payload = {}
        if goal.pose_json:
            try:
                pose_payload = json.loads(goal.pose_json)
            except json.JSONDecodeError:
                pose_payload = {}

        mode = 'absolute_navigation'
        if 'move_forward' in pose_payload:
            mode = 'move_forward'
        elif goal.target_type == 'relative' or pose_payload:
            mode = 'relative_navigation'

        for phase, progress, message in [
            ('STARTED', 0.2, f'{mode} request accepted'),
            ('MOVING', 0.6, f'Navigating in mode={mode}'),
            ('APPROACHING', 0.95, 'Approaching final pose'),
        ]:
            feedback = NavigateSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            goal_handle.publish_feedback(feedback)
            time.sleep(0.2)

        goal_handle.succeed()
        result = NavigateSkill.Result()
        result.success = True
        if mode == 'move_forward':
            dist = pose_payload.get('move_forward', {}).get('distance_m', 0.0)
            result.detail = f'Moved forward {dist}m'
        elif mode == 'relative_navigation':
            result.detail = f'Applied relative pose {json.dumps(pose_payload)}'
        else:
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

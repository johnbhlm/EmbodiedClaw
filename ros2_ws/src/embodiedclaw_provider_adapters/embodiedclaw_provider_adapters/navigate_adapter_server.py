from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import NavigateSkill

REPO_ROOT = Path(__file__).resolve().parents[4]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from providers.provider_factory import get_navigate_provider


class NavigateAdapterServer(Node):
    def __init__(self) -> None:
        super().__init__('navigate_adapter_server')
        self._provider = get_navigate_provider()
        self._action_server = ActionServer(
            self,
            NavigateSkill,
            '/assistant/navigate_skill',
            execute_callback=self.execute_callback,
        )
        self.get_logger().info('Navigate adapter server ready (provider-backed).')

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        try:
            pose_payload = json.loads(goal.pose_json) if goal.pose_json else {}
        except json.JSONDecodeError:
            pose_payload = {}

        if isinstance(pose_payload, dict) and 'move_forward' in pose_payload:
            distance_m = float(pose_payload.get('move_forward', {}).get('distance_m', 0.0))
            mode = 'move_forward'
            nav_result = self._provider.move_forward(distance_m=distance_m, extra=pose_payload)
        elif goal.target_type == 'relative' or goal.pose_json:
            mode = 'relative_navigation'
            nav_result = self._provider.navigate_to(pose_json=goal.pose_json, extra=pose_payload)
        else:
            mode = 'absolute_navigation'
            nav_result = self._provider.navigate_to(location_id=goal.location_id, extra=pose_payload)

        self.get_logger().info(
            f'Navigate adapter request_id={goal.request_id} mode={mode} location_id={goal.location_id}'
        )

        for phase, progress, message in [
            ('STARTED', 0.2, f'{mode} request accepted'),
            ('MOVING', 0.6, f'Provider executing {mode}'),
            ('APPROACHING', 0.95, 'Approaching final pose'),
        ]:
            feedback = NavigateSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            goal_handle.publish_feedback(feedback)
            time.sleep(0.1)

        goal_handle.succeed()
        result = NavigateSkill.Result()
        result.success = bool(nav_result.get('success', True))
        result.detail = str(nav_result.get('detail', 'navigation completed'))
        return result


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NavigateAdapterServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

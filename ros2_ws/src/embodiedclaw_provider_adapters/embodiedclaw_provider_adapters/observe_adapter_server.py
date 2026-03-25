from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import InspectSkill

REPO_ROOT = Path(__file__).resolve().parents[4]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from providers.provider_factory import get_observe_provider

SUPPORTED_MODES = {
    'scene_summary',
    'object_list',
    'object_existence',
    'verify_surface',
    'window_state',
    'light_state',
}


class ObserveAdapterServer(Node):
    def __init__(self) -> None:
        super().__init__('observe_adapter_server')
        self._provider = get_observe_provider()
        self._action_server = ActionServer(
            self,
            InspectSkill,
            '/assistant/inspect_skill',
            execute_callback=self.execute_callback,
        )
        self.get_logger().info('Observe adapter server ready (provider-backed).')

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        inspect_type = (goal.inspect_type or 'scene_summary').strip()
        mode = inspect_type if inspect_type in SUPPORTED_MODES else 'scene_summary'

        try:
            params = json.loads(goal.params_json) if goal.params_json else {}
        except json.JSONDecodeError:
            params = {}

        self.get_logger().info(
            f'Inspect adapter request_id={goal.request_id} inspect_type={inspect_type} mode={mode} target_id={goal.target_id}'
        )

        for phase, progress, message, image_uri in [
            ('STARTED', 0.2, f'Observe request accepted in mode={mode}', ''),
            ('SCANNING', 0.6, f'Collecting observations for target={goal.target_id or "scene"}', 'mock://images/observe_scan.jpg'),
            ('ANALYZING', 0.9, 'Preparing structured finding', 'mock://images/observe_analysis.jpg'),
        ]:
            feedback = InspectSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            feedback.image_uri = image_uri
            goal_handle.publish_feedback(feedback)
            time.sleep(0.1)

        finding = self._provider.observe_scene(goal.target_id, mode=mode, extra=params)

        goal_handle.succeed()
        result = InspectSkill.Result()
        result.success = True
        result.finding = json.dumps(finding)
        if mode in {'window_state', 'light_state', 'scene_summary', 'object_list'}:
            target = goal.target_id or 'scene'
            result.image_uris = [f'mock://images/{mode}_{target}_1.jpg']
        else:
            result.image_uris = []
        return result


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ObserveAdapterServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

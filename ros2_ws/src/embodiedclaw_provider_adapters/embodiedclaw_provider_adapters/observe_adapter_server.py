from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import InspectSkill

REPO_ROOT = Path(__file__).resolve().parents[4]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from providers.provider_config import (
    get_camera_topic,
    get_observe_backend_name,
    get_observe_provider_name,
    get_observe_require_fresh_frame_sec,
    get_save_observe_images,
)
from providers.provider_factory import get_observe_provider

from .frame_buffer import LatestImageBuffer
from .image_artifacts import save_observation_frame

SUPPORTED_MODES = {
    'scene_summary',
    'object_list',
    'object_existence',
    'verify_surface',
    'window_state',
    'light_state',
}

STATUS_FILE = REPO_ROOT / 'runtime_artifacts' / 'observe_camera_status.json'


class ObserveAdapterServer(Node):
    def __init__(self, latest_image_buffer=None) -> None:
        super().__init__('observe_adapter_server')
        provider_name = get_observe_provider_name()
        if provider_name == 'ros_camera' and latest_image_buffer is None:
            latest_image_buffer = LatestImageBuffer(self, get_camera_topic())
        self._latest_image_buffer = latest_image_buffer
        self._provider = get_observe_provider(latest_image_buffer=latest_image_buffer)
        self._save_images = get_save_observe_images()
        self._fresh_frame_sec = get_observe_require_fresh_frame_sec()
        self._action_server = ActionServer(
            self,
            InspectSkill,
            '/assistant/inspect_skill',
            execute_callback=self.execute_callback,
        )
        self._write_status_file()
        self.get_logger().info('Observe adapter server ready (provider-backed).')

    def _camera_status_payload(self) -> dict:
        age = self._latest_image_buffer.get_latest_age_sec() if self._latest_image_buffer is not None else None
        has_recent = (
            self._latest_image_buffer.has_recent_frame(self._fresh_frame_sec)
            if self._latest_image_buffer is not None
            else False
        )
        return {
            'observe_provider': get_observe_provider_name(),
            'camera_topic': get_camera_topic(),
            'observe_backend': get_observe_backend_name(),
            'has_recent_frame': has_recent,
            'latest_frame_age_sec': age,
        }

    def _write_status_file(self) -> None:
        try:
            STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATUS_FILE.write_text(json.dumps(self._camera_status_payload(), ensure_ascii=False), encoding='utf-8')
        except Exception as exc:
            self.get_logger().warning(f'Unable to write camera status file: {exc}')

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

        for phase, progress, message in [
            ('STARTED', 0.2, f'Observe request accepted in mode={mode}'),
            ('SCANNING', 0.6, f'Collecting observations for target={goal.target_id or "scene"}'),
            ('ANALYZING', 0.9, 'Preparing structured finding'),
        ]:
            feedback = InspectSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            feedback.image_uri = ''
            goal_handle.publish_feedback(feedback)
            time.sleep(0.1)

        finding = self._provider.observe_scene(goal.target_id, mode=mode, extra=params)

        image_uris: list[str] = []
        if finding.get('ok') and self._save_images and self._latest_image_buffer is not None:
            latest_frame = self._latest_image_buffer.get_latest_frame()
            if latest_frame is not None:
                image_uri = save_observation_frame(latest_frame)
                if image_uri:
                    image_uris.append(image_uri)

        self._write_status_file()

        goal_handle.succeed()
        result = InspectSkill.Result()
        result.success = bool(finding.get('ok', True))
        result.finding = json.dumps(finding, ensure_ascii=False)
        result.image_uris = image_uris
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

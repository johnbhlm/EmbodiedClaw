from __future__ import annotations

import threading
import time
from typing import Any

from rclpy.node import Node
from sensor_msgs.msg import Image

try:
    from cv_bridge import CvBridge
except ImportError as exc:  # pragma: no cover - depends on runtime image stack
    raise ImportError(
        'cv_bridge is required for EMBODIEDCLAW_OBSERVE_PROVIDER=ros_camera. '
        'Install ros-humble-cv-bridge before launching provider adapters.'
    ) from exc


class LatestImageBuffer:
    """Store the latest camera frame from a ROS2 image topic."""

    def __init__(self, node: Node, topic: str) -> None:
        self._node = node
        self._topic = topic
        self._bridge = CvBridge()
        self._lock = threading.Lock()
        self._latest_frame = None
        self._latest_stamp = None
        self._latest_receive_monotonic = None

        self._subscription = self._node.create_subscription(Image, topic, self._on_image, 10)
        self._node.get_logger().info(f'LatestImageBuffer subscribed topic={topic}')

    def _on_image(self, msg: Image) -> None:
        try:
            frame_bgr = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:  # pragma: no cover - conversion is runtime dependent
            self._node.get_logger().warning(f'Failed to convert image frame: {exc}')
            return

        with self._lock:
            self._latest_frame = frame_bgr
            self._latest_stamp = msg.header.stamp
            self._latest_receive_monotonic = time.monotonic()

    def get_latest_frame(self):
        with self._lock:
            return None if self._latest_frame is None else self._latest_frame.copy()

    def get_latest_age_sec(self) -> float | None:
        with self._lock:
            if self._latest_receive_monotonic is None:
                return None
            return max(0.0, time.monotonic() - self._latest_receive_monotonic)

    def has_recent_frame(self, max_age_sec: float) -> bool:
        age_sec = self.get_latest_age_sec()
        return age_sec is not None and age_sec <= max_age_sec

    def get_latest_stamp(self) -> Any:
        with self._lock:
            return self._latest_stamp

    @property
    def topic(self) -> str:
        return self._topic

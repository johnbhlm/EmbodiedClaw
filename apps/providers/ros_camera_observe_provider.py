from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .base import ObserveProvider
from .observe_backend import ObserveBackend


class RosCameraObserveProvider(ObserveProvider):
    """Observe provider backed by ROS camera frames captured by adapter runtime."""

    def __init__(
        self,
        latest_image_buffer,
        backend: ObserveBackend,
        require_fresh_frame_sec: float = 2.0,
    ) -> None:
        self._latest_image_buffer = latest_image_buffer
        self._backend = backend
        self._require_fresh_frame_sec = require_fresh_frame_sec

    def observe_scene(self, target: str, mode: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._latest_image_buffer.has_recent_frame(self._require_fresh_frame_sec):
            return {
                'ok': False,
                'reason': 'no_recent_frame',
                'target': target,
                'mode': mode,
                'image_available': False,
            }

        frame = self._latest_image_buffer.get_latest_frame()
        if frame is None:
            return {
                'ok': False,
                'reason': 'no_recent_frame',
                'target': target,
                'mode': mode,
                'image_available': False,
            }

        backend_result = self._backend.infer(frame, mode=mode, target=target, extra=extra)
        result = dict(backend_result)
        result.update(
            {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'target': target,
                'mode': mode,
                'image_available': True,
            }
        )
        return result

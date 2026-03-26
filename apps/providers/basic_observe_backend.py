from __future__ import annotations

from typing import Any

from .observe_backend import ObserveBackend


class BasicObserveBackend(ObserveBackend):
    """Structured placeholder backend that runs on real camera frames."""

    def infer(
        self,
        frame_bgr,
        mode: str,
        target: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = extra or {}
        height, width = int(frame_bgr.shape[0]), int(frame_bgr.shape[1])
        image_size = {'width': width, 'height': height}

        if mode == 'scene_summary':
            return {
                'ok': True,
                'summary': 'A real camera frame was captured successfully.',
                'image_size': image_size,
                'mode': 'scene_summary',
            }

        if mode == 'object_list':
            return {
                'ok': True,
                'objects': ['unknown_object'],
                'note': 'Real camera frame received, but object detector is not connected yet.',
                'image_size': image_size,
                'mode': 'object_list',
            }

        if mode == 'object_existence':
            object_name = str(payload.get('object_name', target or '')).strip()
            return {
                'ok': True,
                'object_name': object_name,
                'exists': False,
                'note': 'Real camera frame received, but object detector is not connected yet.',
                'image_size': image_size,
                'mode': 'object_existence',
            }

        if mode == 'verify_surface':
            return {
                'ok': True,
                'tidy': False,
                'note': 'Real camera frame received, but surface verifier is not connected yet.',
                'image_size': image_size,
                'mode': 'verify_surface',
            }

        if mode == 'window_state':
            return {
                'ok': True,
                'target_id': target,
                'closed': None,
                'note': 'Real camera frame received, but window-state detector is not connected yet.',
                'image_size': image_size,
                'mode': 'window_state',
            }

        if mode == 'light_state':
            return {
                'ok': True,
                'target_id': target,
                'off': None,
                'note': 'Real camera frame received, but light-state detector is not connected yet.',
                'image_size': image_size,
                'mode': 'light_state',
            }

        return {
            'ok': True,
            'summary': f'Unsupported observe mode: {mode}',
            'image_size': image_size,
            'mode': mode,
        }

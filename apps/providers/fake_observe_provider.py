from __future__ import annotations

from typing import Any

from providers.base import ObserveProvider


class FakeObserveProvider(ObserveProvider):
    """Deterministic fake observe provider for local orchestration tests."""

    def observe_scene(self, target: str, mode: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = extra or {}

        if mode == 'scene_summary':
            return {'summary': 'table and chair visible'}

        if mode == 'object_list':
            return {'objects': ['apple', 'cup', 'book']}

        if mode == 'object_existence':
            object_name = str(payload.get('object_name', target or '')).strip() or 'apple'
            return {'object_name': object_name, 'exists': object_name.lower() == 'apple'}

        if mode == 'verify_surface':
            return {'tidy': True}

        if mode == 'window_state':
            target_id = target or str(payload.get('target_id', 'window_01'))
            return {'target_id': target_id, 'closed': True}

        if mode == 'light_state':
            target_id = target or str(payload.get('target_id', 'light_01'))
            return {'target_id': target_id, 'off': True}

        return {'summary': f'unsupported_mode={mode}'}

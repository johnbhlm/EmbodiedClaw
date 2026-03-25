from __future__ import annotations

from typing import Any

from providers.base import NavigateProvider


class FakeNavigateProvider(NavigateProvider):
    """Deterministic fake navigate provider for local orchestration tests."""

    def navigate_to(
        self,
        location_id: str | None = None,
        pose_json: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if location_id:
            return {'success': True, 'detail': f'navigated to {location_id}'}

        if pose_json:
            return {'success': True, 'detail': 'rotated via relative pose'}

        return {'success': True, 'detail': 'navigated to target'}

    def move_forward(self, distance_m: float, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        return {'success': True, 'detail': f'moved forward {distance_m:.1f}m'}

from __future__ import annotations

from typing import Any

from .base import NavigateProvider


class UnitreeSDKNavigateProvider(NavigateProvider):
    """Future Unitree SDK-backed navigation/motion provider placeholder."""

    def navigate_to(
        self,
        location_id: str | None = None,
        pose_json: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError(
            'TODO(M3+): integrate VLN/SDK-backed absolute/relative navigation execution.'
        )

    def move_forward(self, distance_m: float, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError('TODO(M3+): integrate SDK-backed forward motion primitive.')

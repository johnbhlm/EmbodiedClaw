from __future__ import annotations

from typing import Any

from providers.base import ObserveProvider


class CameraObserveProvider(ObserveProvider):
    """Future real camera-backed observation provider placeholder."""

    def observe_scene(self, target: str, mode: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(
            'TODO(M3+): integrate camera/VLA perception runtime and structured observation output.'
        )

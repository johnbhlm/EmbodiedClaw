from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ObserveProvider(ABC):
    """Provider abstraction for scene observation capabilities."""

    @abstractmethod
    def observe_scene(self, target: str, mode: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Observe a target scene/object using a provider-specific mode."""


class NavigateProvider(ABC):
    """Provider abstraction for navigation/motion capabilities."""

    @abstractmethod
    def navigate_to(
        self,
        location_id: str | None = None,
        pose_json: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Navigate to an absolute location or relative pose payload."""

    @abstractmethod
    def move_forward(self, distance_m: float, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Move forward by a relative distance in meters."""

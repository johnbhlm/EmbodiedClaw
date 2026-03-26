from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ObserveBackend(ABC):
    """Inference backend abstraction for observe providers."""

    @abstractmethod
    def infer(
        self,
        frame_bgr,
        mode: str,
        target: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return structured observation output from a BGR frame."""

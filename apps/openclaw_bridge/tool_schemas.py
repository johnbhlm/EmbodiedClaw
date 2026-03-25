from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolCallResult:
    ok: bool
    mode: str
    message: str
    task_id: str | None = None
    raw: dict[str, Any] | None = None

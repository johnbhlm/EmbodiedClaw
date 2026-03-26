from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OpenClawMessageResponse:
    ok: bool
    mode: str
    reply_text: str
    task_id: str | None = None
    needs_polling: bool = False
    terminal: bool = True
    image_uris: list[str] = field(default_factory=list)
    primary_image_uri: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class OpenClawPollResponse:
    ok: bool
    mode: str
    reply_text: str
    task_id: str | None = None
    terminal: bool = False
    progress: float | None = None
    image_uris: list[str] = field(default_factory=list)
    primary_image_uri: str | None = None
    raw: dict[str, Any] | None = None

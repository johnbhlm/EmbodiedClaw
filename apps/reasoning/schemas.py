from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

InterpretationStatus = Literal['executable', 'clarification_needed', 'unsupported', 'scheduled_task']


@dataclass(frozen=True)
class InterpretationResult:
    status: InterpretationStatus
    normalized_command: str
    task_spec: dict[str, Any] | None = None
    clarification_question: str | None = None
    reason: str | None = None
    schedule: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClarificationResult:
    needs_clarification: bool
    question: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

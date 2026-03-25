from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TaskSpec:
    task_id: str
    task_type: str
    task_payload: dict[str, Any] = field(default_factory=dict)
    priority: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SkillStep:
    skill_name: str
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ''
    labels: list[str] = field(default_factory=list)
    branch: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

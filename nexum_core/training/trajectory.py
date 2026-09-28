from dataclasses import dataclass, field
from typing import Any

@dataclass
class Trajectory:
    task: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    verification: dict[str, Any] = field(default_factory=dict)
    success: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def record(self, kind: str, payload: dict[str, Any]):
        target = {
            "message": self.messages,
            "action": self.actions,
            "observation": self.observations,
        }.get(kind)
        if target is not None:
            target.append(payload)

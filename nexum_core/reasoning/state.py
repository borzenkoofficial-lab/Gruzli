from dataclasses import dataclass, field
from typing import Any

@dataclass
class ExecutionState:
    task: str
    phase: str = "planning"
    iteration: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    verified: bool = False
    errors: list[str] = field(default_factory=list)

    def event(self, kind: str, **data):
        self.events.append({"kind": kind, **data})

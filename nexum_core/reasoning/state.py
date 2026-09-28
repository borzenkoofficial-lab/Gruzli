from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ExecutionState:
    task: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    phase: str = "planning"
    iteration: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    verified: bool = False
    errors: list[str] = field(default_factory=list)

    def event(self, kind: str, **data):
        self.events.append({
            "id": str(uuid4()),
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            **data,
        })

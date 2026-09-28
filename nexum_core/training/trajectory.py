from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Trajectory:
    task: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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
            target.append({
                "event_id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **payload,
            })
        elif kind == "verification":
            self.verification = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **payload,
            }
        elif kind == "metadata":
            self.metadata.update(payload)

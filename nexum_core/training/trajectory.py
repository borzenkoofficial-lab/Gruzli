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
    council: dict[str, Any] = field(default_factory=dict)

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
        elif kind == "council":
            self.council.update(payload)

    def to_training_record(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "messages": self.messages,
            "actions": self.actions,
            "observations": self.observations,
            "verification": self.verification,
            "success": self.success,
            "metadata": self.metadata,
            "council": self.council,
        }

from dataclasses import dataclass, field
from typing import Any

@dataclass
class Trajectory:
    task: str
    messages: list[dict[str, Any]]
    actions: list[dict[str, Any]] = field(default_factory=list)
    outcome: str = ""
    success: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"task": self.task, "messages": self.messages, "actions": self.actions,
                "outcome": self.outcome, "success": self.success, "metadata": self.metadata}

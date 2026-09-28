from dataclasses import dataclass, field
from typing import Any

@dataclass
class Action:
    id: str
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    purpose: str = ""
    success_condition: str = ""

@dataclass
class Observation:
    action_id: str
    ok: bool
    output: Any = None
    error: str | None = None

@dataclass
class AgentDecision:
    kind: str
    content: str = ""
    actions: list[Action] = field(default_factory=list)

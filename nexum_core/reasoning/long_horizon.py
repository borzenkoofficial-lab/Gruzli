from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class LongHorizonPlan:
    goal: str
    steps: list[str]
    completed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

class LongHorizonPlanner:
    def create(self, goal: str) -> LongHorizonPlan:
        return LongHorizonPlan(goal, [
            "understand goal and constraints",
            "inspect available context and tools",
            "form a minimal executable plan",
            "execute and observe",
            "verify objective result",
            "repair failures",
            "store verified experience",
        ])

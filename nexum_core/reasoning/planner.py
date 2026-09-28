from dataclasses import dataclass
from typing import Any

@dataclass
class PlanStep:
    id: str
    objective: str
    success_condition: str
    tools: list[str]

@dataclass
class Plan:
    objective: str
    steps: list[PlanStep]

class Planner:
    def build(self, task: str, agents: list[str]) -> Plan:
        return Plan(
            objective=task,
            steps=[PlanStep("step-1", task, "Observable evidence confirms completion", [])]
        )

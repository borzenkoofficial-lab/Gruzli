from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class RepairPlan:
    category: str
    instruction: str
    evidence: list[str]
    file: str | None = None
    line: int | None = None

class RepairPlanner:
    """Turns parsed failures into deterministic repair tasks; it never edits code."""
    def plan(self, details: dict[str, Any]) -> RepairPlan:
        parsed = details.get("parsed_error") or {}
        category = str(parsed.get("category") or "execution")
        file_name = parsed.get("file")
        line = parsed.get("line")
        evidence = [str(x) for x in (parsed.get("evidence") or [])]
        location = f"{file_name}:{line}" if file_name and line else (file_name or "project")
        instruction = f"Inspect {location}; fix the {category} failure using the supplied evidence; rerun the failing check."
        return RepairPlan(category, instruction, evidence, file_name, line)

@dataclass
class RepairCycle:
    attempt: int
    plan: RepairPlan
    mutation_applied: bool
    verification_ok: bool

class AutonomousRepairLoop:
    """Runs verification and delegates actual mutation to an explicit callback."""
    def __init__(self, verify: Callable[[], dict[str, Any]], mutate: Callable[[RepairPlan], bool], max_attempts: int = 3):
        self.verify = verify
        self.mutate = mutate
        self.max_attempts = max(1, max_attempts)
        self.planner = RepairPlanner()

    def run(self) -> dict[str, Any]:
        cycles: list[RepairCycle] = []
        for attempt in range(1, self.max_attempts + 1):
            result = self.verify()
            if result.get("ok"):
                return {"ok": True, "attempts": cycles, "verification": result}
            plan = self.planner.plan(result)
            applied = bool(self.mutate(plan))
            after = self.verify() if applied else {"ok": False, "skipped": True}
            cycle = RepairCycle(attempt, plan, applied, bool(after.get("ok")))
            cycles.append(cycle)
            if cycle.verification_ok:
                return {"ok": True, "attempts": cycles, "verification": after}
            if not applied:
                break
        return {"ok": False, "attempts": cycles, "verification": self.verify()}

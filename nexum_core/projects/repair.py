from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .error_parser import ParsedFailure
from .runtime import ProjectRuntime


@dataclass
class RepairAttempt:
    ok: bool
    category: str
    message: str
    before: dict[str, Any]
    after: dict[str, Any]


class RepairEngine:
    def __init__(self, runtime: ProjectRuntime, max_attempts: int = 3):
        self.runtime = runtime
        self.max_attempts = max(1, max_attempts)

    def verify_and_repair(self) -> list[RepairAttempt]:
        attempts: list[RepairAttempt] = []
        for _ in range(self.max_attempts):
            before = self.runtime.build().__dict__
            if before["ok"]:
                test = self.runtime.test().__dict__
                attempts.append(RepairAttempt(test["ok"], "test", "verification", before, test))
                if test["ok"]:
                    return attempts
                continue
            parsed = before["details"].get("parsed_error", {})
            attempts.append(RepairAttempt(False, parsed.get("category", "build"), parsed.get("message", "build failed"), before, {}))
            break
        return attempts

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .runtime import ProjectRuntime


@dataclass
class RepairRequest:
    category: str
    message: str
    file: str | None
    line: int | None
    column: int | None
    evidence: list[str]
    instruction: str


@dataclass
class RepairAttempt:
    ok: bool
    category: str
    message: str
    before: dict[str, Any]
    after: dict[str, Any]
    repair_request: RepairRequest | None = None


class RepairEngine:
    """Verification loop plus a structured handoff for an agent that can edit files.

    The engine never pretends that a repair happened. A mutation only counts when
    the supplied repair callback actually performs it and the subsequent verifier passes.
    """

    def __init__(self, runtime: ProjectRuntime, max_attempts: int = 3):
        self.runtime = runtime
        self.max_attempts = max(1, max_attempts)

    def _request(self, details: dict[str, Any]) -> RepairRequest:
        parsed = details.get("parsed_error", {})
        category = parsed.get("category", "execution")
        message = parsed.get("message") or details.get("error") or "verification failed"
        file_name = parsed.get("file")
        line = parsed.get("line")
        column = parsed.get("column")
        evidence = parsed.get("evidence") or []
        instruction = (
            f"Inspect {file_name}:{line}:{column} and correct the {category} failure, "
            "then rerun the failing verification."
            if file_name and line
            else f"Inspect the failure evidence and correct the {category} failure, then rerun verification."
        )
        return RepairRequest(category, message, file_name, line, column, evidence, instruction)

    def verify_and_repair(
        self,
        repair: Callable[[RepairRequest], bool] | None = None,
    ) -> list[RepairAttempt]:
        attempts: list[RepairAttempt] = []
        for _ in range(self.max_attempts):
            before_result = self.runtime.build()
            before = before_result.__dict__
            if before_result.ok:
                test_result = self.runtime.test()
                after = test_result.__dict__
                if test_result.ok:
                    attempts.append(RepairAttempt(True, "verification", "build and test passed", before, after))
                    return attempts
                request = self._request(test_result.details)
                attempts.append(RepairAttempt(False, request.category, request.message, before, after, request))
            else:
                request = self._request(before_result.details)
                attempts.append(RepairAttempt(False, request.category, request.message, before, {}, request))

            if repair is None:
                return attempts
            if not repair(request):
                return attempts

        return attempts

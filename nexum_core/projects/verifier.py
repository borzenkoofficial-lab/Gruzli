from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .runtime import ProjectRuntime


@dataclass
class VerificationReport:
    ok: bool
    checks: list[dict[str, Any]]


class ProjectVerifier:
    def __init__(self, workspace: str):
        self.root = Path(workspace).resolve()
        self.runtime = ProjectRuntime(str(self.root))

    def verify(self, build: bool = True, test: bool = True) -> VerificationReport:
        checks = []
        if build:
            result = self.runtime.build()
            checks.append({"name": "build", "ok": result.ok, "details": result.details})
        if test:
            result = self.runtime.test()
            checks.append({"name": "test", "ok": result.ok, "details": result.details})
        return VerificationReport(bool(checks) and all(c["ok"] for c in checks), checks)

    def verify_lifecycle(self) -> VerificationReport:
        lifecycle = self.runtime.lifecycle(install=True)
        checks = []
        for step in lifecycle["steps"]:
            checks.append({
                "name": step["operation"],
                "ok": step["ok"],
                "details": step["details"],
            })
        return VerificationReport(bool(checks) and lifecycle["ok"], checks)

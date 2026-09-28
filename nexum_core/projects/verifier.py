from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .runtime import ProjectRuntime


@dataclass
class VerificationReport:
    ok: bool
    checks: list[dict[str, Any]]

    @property
    def evidence(self) -> list[Any]:
        return [check.get("details") for check in self.checks if check.get("ok")]


class ProjectVerifier:
    def __init__(self, workspace: str):
        self.root = Path(workspace).resolve()
        self.runtime = ProjectRuntime(str(self.root))

    def verify(self, build: bool = True, test: bool = True) -> VerificationReport:
        checks: list[dict[str, Any]] = []
        if build:
            result = self.runtime.build()
            checks.append({"name": "build", "ok": result.ok, "details": result.details})
        if test:
            result = self.runtime.test()
            checks.append({"name": "test", "ok": result.ok, "details": result.details})
        return VerificationReport(bool(checks) and all(c["ok"] for c in checks), checks)

    def verify_python(self) -> VerificationReport:
        result = self.runtime.command("python", ["-m", "compileall", "-q", "."], 120)
        return VerificationReport(
            result.ok,
            [{"name": "python_compile", "ok": result.ok, "details": result.details}],
        )

    def verify_node(self) -> VerificationReport:
        info = self.runtime.inspect().details
        if not info["has_package_json"]:
            return VerificationReport(False, [{
                "name": "node_project",
                "ok": False,
                "details": {"error": "package.json not found"},
            }])
        build = self.runtime.build()
        return VerificationReport(build.ok, [{
            "name": "node_build",
            "ok": build.ok,
            "details": build.details,
        }])

    def verify_project(self) -> VerificationReport:
        return self.verify(build=True, test=True)

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

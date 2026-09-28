from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..tools.command_runner import RunCommand
from ..tools.executor import ToolCall, ToolExecutor
from .dev_server import DevServerManager
from .manager import ProjectManager


@dataclass
class ProjectResult:
    ok: bool
    operation: str
    details: dict[str, Any]


class ProjectRuntime:
    def __init__(self, workspace: str):
        self.root = Path(workspace).resolve()
        self.manager = ProjectManager(str(self.root))
        self.executor = ToolExecutor(self._registry())
        self.preview = DevServerManager(str(self.root))

    def _registry(self):
        from ..tools.registry import ToolRegistry
        registry = ToolRegistry()
        registry.register(RunCommand(str(self.root)))
        return registry

    def inspect(self) -> ProjectResult:
        return ProjectResult(True, "inspect", self.manager.inspect())

    def command(self, command: str, args: list[str] | None = None, timeout: int = 30) -> ProjectResult:
        result = self.executor.execute(ToolCall("run_command", {
            "command": command, "args": args or [], "timeout": timeout
        }))
        return ProjectResult(result.ok, "command", {"output": result.output, "error": result.error})

    def install(self) -> ProjectResult:
        info = self.manager.inspect()
        if not info["has_package_json"]:
            return ProjectResult(False, "install", {"error": "package.json not found"})
        return self.command("npm", ["install"], 120)

    def build(self) -> ProjectResult:
        info = self.manager.inspect()
        if info["has_package_json"]:
            return self.command("npm", ["run", "build"], 120)
        if info["has_pyproject"]:
            return self.command("python", ["-m", "compileall", "-q", "."], 120)
        return ProjectResult(False, "build", {"error": "No supported project manifest found"})

    def test(self) -> ProjectResult:
        info = self.manager.inspect()
        if info["has_package_json"]:
            return self.command("npm", ["test"], 120)
        if info["has_pyproject"]:
            return self.command("pytest", ["-q"], 120)
        return ProjectResult(False, "test", {"error": "No supported project manifest found"})

    def start_preview(self) -> ProjectResult:
        info = self.manager.inspect()
        if not info["has_package_json"]:
            return ProjectResult(False, "preview", {"error": "Preview currently supports package.json projects"})
        result = self.preview.start("npm", ["run", "dev", "--", "--host", "127.0.0.1"])
        return ProjectResult(result.ok, "preview", result.__dict__)

    def stop_preview(self, pid: int) -> ProjectResult:
        return ProjectResult(self.preview.stop(pid), "preview_stop", {"pid": pid})

    def lifecycle(self, install: bool = True) -> dict[str, Any]:
        steps = [self.inspect()]
        if install:
            steps.append(self.install())
            if not steps[-1].ok:
                return {"ok": False, "steps": [s.__dict__ for s in steps]}
        steps.append(self.build())
        if not steps[-1].ok:
            return {"ok": False, "steps": [s.__dict__ for s in steps]}
        steps.append(self.test())
        return {"ok": all(s.ok for s in steps), "steps": [s.__dict__ for s in steps]}

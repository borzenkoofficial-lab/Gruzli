from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..tools.command_runner import RunCommand
from ..tools.executor import ToolExecutor, ToolCall
from .manager import ProjectManager


@dataclass
class ProjectResult:
    ok: bool
    operation: str
    details: dict


class ProjectRuntime:
    def __init__(self, workspace: str):
        self.root = Path(workspace).resolve()
        self.manager = ProjectManager(str(self.root))
        self.executor = ToolExecutor(self._registry())

    def _registry(self):
        from ..tools.registry import ToolRegistry
        registry = ToolRegistry()
        registry.register(RunCommand(str(self.root)))
        return registry

    def inspect(self) -> ProjectResult:
        return ProjectResult(True, "inspect", self.manager.inspect())

    def command(self, command: str, args: list[str] | None = None, timeout: int = 30) -> ProjectResult:
        result = self.executor.execute(
            ToolCall("run_command", {"command": command, "args": args or [], "timeout": timeout})
        )
        return ProjectResult(result.ok, "command", {
            "output": result.output,
            "error": result.error,
        })

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

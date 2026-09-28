from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..tools.command_runner import RunCommand
from ..tools.executor import ToolCall, ToolExecutor
from .dev_server import DevServerManager
from .error_parser import ErrorParser
from .manager import ProjectManager
from .state import ProjectState


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
        self.state = ProjectState(str(self.root))
        self.errors = ErrorParser()

    def _registry(self):
        from ..tools.registry import ToolRegistry
        registry = ToolRegistry()
        registry.register(RunCommand(str(self.root)))
        return registry

    def inspect(self) -> ProjectResult:
        info = self.manager.inspect()
        info["package_manager"] = self.package_manager()
        info["state"] = self.state.get()
        return ProjectResult(True, "inspect", info)

    def package_manager(self) -> str | None:
        if (self.root / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (self.root / "yarn.lock").exists():
            return "yarn"
        if (self.root / "package-lock.json").exists():
            return "npm"
        if (self.root / "package.json").exists():
            return "npm"
        return None

    def command(self, command: str, args: list[str] | None = None, timeout: int = 30) -> ProjectResult:
        result = self.executor.execute(ToolCall("run_command", {
            "command": command, "args": args or [], "timeout": timeout
        }))
        details = {"output": result.output, "error": result.error}
        return ProjectResult(result.ok, "command", details)

    def install(self) -> ProjectResult:
        manager = self.package_manager()
        if not manager:
            return ProjectResult(False, "install", {"error": "No supported package manifest found"})
        self.state.set("installing", package_manager=manager)
        if manager == "npm" and (self.root / "package-lock.json").exists():
            args = ["ci", "--ignore-scripts"]
        else:
            args = ["install", "--ignore-scripts"]
        result = self.command(manager, args, 120)
        if not result.ok:
            result.details["parsed_error"] = self.errors.parse(result.details).__dict__
        self.state.set("ready" if result.ok else "failed", operation="install")
        return ProjectResult(result.ok, "install", result.details)

    def build(self) -> ProjectResult:
        info = self.manager.inspect()
        if info["has_package_json"]:
            manager = self.package_manager() or "npm"
            self.state.set("building", operation="build")
            result = self.command(manager, ["run", "build"], 120)
        elif info["has_pyproject"]:
            self.state.set("building", operation="build")
            result = self.command("python", ["-m", "compileall", "-q", "."], 120)
        else:
            return ProjectResult(False, "build", {"error": "No supported project manifest found"})
        if not result.ok:
            result.details["parsed_error"] = self.errors.parse(result.details).__dict__
        self.state.set("ready" if result.ok else "failed", operation="build")
        return ProjectResult(result.ok, "build", result.details)

    def test(self) -> ProjectResult:
        info = self.manager.inspect()
        if info["has_package_json"]:
            manager = self.package_manager() or "npm"
            self.state.set("testing", operation="test")
            result = self.command(manager, ["test"], 120)
        elif info["has_pyproject"]:
            self.state.set("testing", operation="test")
            result = self.command("pytest", ["-q"], 120)
        else:
            return ProjectResult(False, "test", {"error": "No supported project manifest found"})
        if not result.ok:
            result.details["parsed_error"] = self.errors.parse(result.details).__dict__
        self.state.set("ready" if result.ok else "failed", operation="test")
        return ProjectResult(result.ok, "test", result.details)

    def start_preview(self) -> ProjectResult:
        info = self.manager.inspect()
        if not info["has_package_json"]:
            return ProjectResult(False, "preview", {"error": "Preview currently supports package.json projects"})
        manager = self.package_manager() or "npm"
        result = self.preview.start(manager, ["run", "dev", "--", "--host", "127.0.0.1"])
        self.state.set("running" if result.ok else "failed", pid=result.pid)
        return ProjectResult(result.ok, "preview", result.__dict__)

    def stop_preview(self, pid: int) -> ProjectResult:
        ok = self.preview.stop(pid)
        if ok:
            self.state.set("stopped", pid=pid)
        return ProjectResult(ok, "preview_stop", {"pid": pid})

    def checkpoint(self, label: str = "before-change") -> dict[str, Any]:
        return self.state.snapshot(label).__dict__

    def restore(self, snapshot_id: str) -> ProjectResult:
        ok = self.state.restore(snapshot_id)
        if ok:
            self.state.set("ready", restored_from=snapshot_id)
        return ProjectResult(ok, "restore", {"snapshot_id": snapshot_id})

    def verify_and_repair(self, max_attempts: int = 3) -> dict[str, Any]:
        from .repair import RepairEngine
        checkpoint = self.checkpoint("before-verification-repair")
        attempts = RepairEngine(self, max_attempts).verify_and_repair()
        ok = bool(attempts) and attempts[-1].ok
        if not ok and checkpoint.get("id"):
            self.restore(checkpoint["id"])
        return {
            "ok": ok,
            "checkpoint": checkpoint,
            "attempts": [a.__dict__ for a in attempts],
        }

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

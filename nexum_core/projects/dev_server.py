from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ProcessResult:
    ok: bool
    pid: int | None
    command: list[str]
    error: str | None = None


class DevServerManager:
    def __init__(self, workspace: str):
        self.workspace = Path(workspace).resolve()
        self._processes: dict[int, subprocess.Popen] = {}

    def start(self, command: str = "npm", args: list[str] | None = None) -> ProcessResult:
        if command not in {"npm", "pnpm", "python"}:
            return ProcessResult(False, None, [], f"Command is not allowed for preview: {command}")
        argv = [command, *(args or [])]
        try:
            process = subprocess.Popen(
                argv,
                cwd=self.workspace,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False,
            )
        except OSError as exc:
            return ProcessResult(False, None, argv, f"{type(exc).__name__}: {exc}")
        self._processes[process.pid] = process
        return ProcessResult(True, process.pid, argv)

    def stop(self, pid: int) -> bool:
        process = self._processes.pop(pid, None)
        if process is None:
            return False
        if process.poll() is None:
            process.terminate()
        return True

    def status(self, pid: int) -> dict[str, Any]:
        process = self._processes.get(pid)
        if process is None:
            return {"known": False}
        return {"known": True, "pid": pid, "running": process.poll() is None, "exit_code": process.poll()}

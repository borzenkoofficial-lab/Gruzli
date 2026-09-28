from __future__ import annotations

import subprocess
from pathlib import Path

from .base import Tool


class RunCommand(Tool):
    name = "run_command"
    description = "Run an allowlisted development command inside the workspace without a shell."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "args": {"type": "array", "items": {"type": "string"}},
            "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    ALLOWED = {"python", "python3", "node", "npm", "npx", "pnpm", "pytest"}

    def __init__(self, workspace: str):
        self.workspace = Path(workspace).resolve()

    def execute(self, command: str, args: list[str] | None = None, timeout: int = 30) -> dict:
        if command not in self.ALLOWED:
            raise ValueError(f"Command is not allowlisted: {command}")
        args = [str(item) for item in (args or [])]
        timeout = max(1, min(int(timeout), 120))
        proc = subprocess.run(
            [command, *args],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return {
            "command": [command, *args],
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-20000:],
            "stderr": proc.stderr[-20000:],
        }

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .base import Tool
from ..projects.sandbox import Sandbox


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

    ALLOWED = {"python", "python3", "node", "npm", "npx", "pnpm", "yarn", "pytest"}

    def __init__(self, workspace: str):
        self.workspace = Path(workspace).resolve()
        self.sandbox = Sandbox(str(self.workspace))

    def execute(self, command: str, args: list[str] | None = None, timeout: int = 30) -> dict:
        self.sandbox.validate_command(command, timeout)
        args = [str(item) for item in (args or [])]
        timeout = max(1, min(int(timeout), self.sandbox.policy.max_timeout))
        env = {
            key: value for key, value in os.environ.items()
            if key in {"PATH", "HOME", "USERPROFILE", "SystemRoot", "TEMP", "TMP", "LANG", "LC_ALL"}
        }
        env["NEXUM_WORKSPACE"] = str(self.workspace)
        try:
            proc = subprocess.run(
                [command, *args],
                cwd=self.workspace,
                env=env,
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
        except subprocess.TimeoutExpired as exc:
            return {
                "command": [command, *args],
                "exit_code": -1,
                "stdout": str(exc.stdout or "")[-20000:],
                "stderr": "TIMEOUT",
            }

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .base import Tool


class CodeRunner(Tool):
    name = "run_python"
    description = "Run a Python snippet in a temporary directory with a strict timeout."
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "timeout": {"type": "integer", "minimum": 1, "maximum": 30},
        },
        "required": ["code"],
        "additionalProperties": False,
    }

    def execute(self, code: str, timeout: int = 10) -> dict:
        timeout = max(1, min(int(timeout), 30))
        with tempfile.TemporaryDirectory(prefix="nexum-run-") as d:
            p = Path(d) / "main.py"
            p.write_text(code, encoding="utf-8")
            try:
                proc = subprocess.run(
                    ["python", str(p)],
                    cwd=d,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=False,
                )
                return {
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout[-12000:],
                    "stderr": proc.stderr[-12000:],
                }
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or ""
                stderr = exc.stderr or ""
                if isinstance(stdout, bytes):
                    stdout = stdout.decode("utf-8", errors="replace")
                if isinstance(stderr, bytes):
                    stderr = stderr.decode("utf-8", errors="replace")
                return {
                    "exit_code": -1,
                    "stdout": stdout[-12000:],
                    "stderr": f"{stderr[-12000:]}\nTIMEOUT",
                }

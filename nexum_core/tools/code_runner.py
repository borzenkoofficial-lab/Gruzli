from __future__ import annotations
import subprocess, tempfile
from pathlib import Path
from .base import Tool

class CodeRunner(Tool):
    name = "run_python"
    description = "Run a Python snippet in an isolated temporary directory with a strict timeout."

    def execute(self, code: str, timeout: int = 10) -> dict:
        timeout = max(1, min(int(timeout), 30))
        with tempfile.TemporaryDirectory(prefix="nexum-run-") as d:
            p = Path(d) / "main.py"
            p.write_text(code, encoding="utf-8")
            try:
                proc = subprocess.run(
                    ["python", str(p)],
                    cwd=d, capture_output=True, text=True, timeout=timeout
                )
                return {"exit_code": proc.returncode, "stdout": proc.stdout[-12000:], "stderr": proc.stderr[-12000:]}
            except subprocess.TimeoutExpired as exc:
                return {"exit_code": -1, "stdout": (exc.stdout or "")[-12000:], "stderr": "TIMEOUT"}

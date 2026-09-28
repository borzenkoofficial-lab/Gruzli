from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(command: list[str], cwd: Path, timeout: int = 120) -> dict:
    try:
        p = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, shell=False)
        return {"command": command, "exit_code": p.returncode, "stdout": p.stdout[-12000:], "stderr": p.stderr[-12000:]}
    except subprocess.TimeoutExpired:
        return {"command": command, "exit_code": -1, "stdout": "", "stderr": "TIMEOUT"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".")
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    checks = []
    for name, command in [
        ("python_compile", ["python", "-m", "compileall", "-q", "nexum_core"]),
        ("pytest", ["python", "-m", "pytest", "-q"]),
    ]:
        result = run(command, root)
        checks.append({"name": name, **result})
    ok = all(item["exit_code"] == 0 for item in checks)
    print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

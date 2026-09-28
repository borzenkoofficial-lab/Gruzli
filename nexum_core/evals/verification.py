from __future__ import annotations

from typing import Any


def check_exit_code(result: Any, expected: int = 0) -> dict:
    code = result.get("exit_code") if isinstance(result, dict) else None
    return {"name": "exit_code", "ok": code == expected, "expected": expected, "actual": code}


def check_text(result: Any, expected: str) -> dict:
    text = str(result)
    return {"name": "text", "ok": expected in text, "expected": expected}


def aggregate(checks: list[dict]) -> dict:
    return {"ok": bool(checks) and all(c["ok"] for c in checks), "checks": checks}

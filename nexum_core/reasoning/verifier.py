from dataclasses import dataclass
from typing import Any


@dataclass
class Verification:
    ok: bool
    evidence: list[Any]
    errors: list[str]
    checks: list[dict[str, Any]]


class Verifier:
    def verify(self, outputs: list[Any], required: str) -> Verification:
        evidence = [item for item in outputs if item is not None]
        failed = [item for item in evidence if isinstance(item, dict) and item.get("ok") is False]
        if failed:
            return Verification(False, evidence, ["Structured execution result reports failure"], [{"type": "structured_status", "ok": False, "failed": failed}])
        if not evidence:
            return Verification(False, [], ["No observable execution output"], [])

        condition = required.strip()
        checks: list[dict[str, Any]] = []

        if not condition or condition.lower().startswith("observable evidence confirms"):
            checks.append({"type": "presence", "ok": True})
            return Verification(True, evidence, [], checks)

        normalized = " ".join(str(item) for item in evidence).lower()
        words = [
            w.strip(".,:;()[]{}'\"")
            for w in condition.lower().split()
            if len(w.strip(".,:;()[]{}'\"")) >= 4
        ]
        missing = [word for word in words if word not in normalized]
        checks.append({
            "type": "content",
            "required": condition,
            "matched": len(words) - len(missing),
            "missing": missing,
        })
        if missing:
            return Verification(
                False,
                evidence,
                [f"Success condition not evidenced: {condition}"],
                checks,
            )
        return Verification(True, evidence, [], checks)

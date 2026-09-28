from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Evidence:
    kind: str
    ok: bool
    source: str
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class VerificationResult:
    ok: bool
    score: float
    evidence: list[Evidence]
    failures: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "score": self.score,
            "evidence": [e.__dict__ for e in self.evidence],
            "failures": self.failures,
        }

def verify_checks(checks: list[dict[str, Any]], required: set[str] | None = None) -> VerificationResult:
    required = required or {str(c.get("name")) for c in checks}
    evidence = [
        Evidence(str(c.get("name", "unknown")), bool(c.get("ok")), "project_verifier", c.get("details") or {})
        for c in checks
    ]
    failures = [e.kind for e in evidence if not e.ok]
    present = {e.kind for e in evidence}
    coverage = len(present & required) / max(1, len(required))
    passed = sum(1 for e in evidence if e.ok)
    quality = passed / max(1, len(evidence))
    score = round(0.6 * coverage + 0.4 * quality, 3)
    return VerificationResult(not failures and required.issubset(present), score, evidence, failures)

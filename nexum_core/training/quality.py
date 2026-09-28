from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import Any

@dataclass
class QualityDecision:
    accepted: bool
    score: float
    reasons: list[str]
    fingerprint: str

class DatasetQuality:
    def __init__(self, min_score: float = 0.7):
        self.min_score = min_score

    def evaluate(self, record: dict[str, Any]) -> QualityDecision:
        task = str(record.get("task") or record.get("input") or "").strip()
        output = self._output(record)
        verification = record.get("verification") or {}
        score = 0.0
        reasons: list[str] = []
        if task:
            score += 0.2
        else:
            reasons.append("missing_task")
        if output:
            score += 0.2
        else:
            reasons.append("missing_output")
        if record.get("success") and verification.get("ok"):
            score += 0.45
        else:
            reasons.append("not_verified")
        if record.get("actions") or record.get("observations"):
            score += 0.15
        else:
            reasons.append("no_execution_trace")
        fingerprint = hashlib.sha256((task + "\n" + output).encode("utf-8")).hexdigest()
        return QualityDecision(score >= self.min_score, round(score, 3), reasons, fingerprint)

    @staticmethod
    def _output(record: dict[str, Any]) -> str:
        messages = record.get("messages") or []
        for item in reversed(messages):
            if item.get("role") in {"assistant", "model"} and item.get("content"):
                return str(item["content"]).strip()
        return str(record.get("output") or "").strip()

    def filter(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        accepted: list[dict[str, Any]] = []
        seen: set[str] = set()
        for record in records:
            decision = self.evaluate(record)
            if decision.accepted and decision.fingerprint not in seen:
                enriched = dict(record)
                enriched["quality"] = {"score": decision.score, "reasons": decision.reasons, "fingerprint": decision.fingerprint}
                accepted.append(enriched)
                seen.add(decision.fingerprint)
        return accepted

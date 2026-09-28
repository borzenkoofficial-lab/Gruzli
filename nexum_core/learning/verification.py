from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass
class LessonVerification:
    ok: bool
    score: float
    checks: list[dict]
    reason: str

def verify_lesson(answer: str) -> LessonVerification:
    text = (answer or "").strip()
    checks = []
    substantive = len(re.findall(r"\S+", text)) >= 12
    checks.append({"name": "substantive", "ok": substantive})
    uncertainty = bool(re.search(r"\b(I don't know|cannot verify|не знаю|не могу проверить)\b", text, re.I))
    checks.append({"name": "uncertainty_disclosed", "ok": True, "flagged": uncertainty})
    score = 0.85 if substantive and not uncertainty else (0.72 if substantive else 0.2)
    return LessonVerification(score >= 0.7, score, checks, "sufficient lesson" if score >= 0.7 else "insufficient lesson")

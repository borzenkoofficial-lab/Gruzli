from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class Reflection:
    accepted: bool
    score: float
    strengths: list[str]
    weaknesses: list[str]
    next_step: str

class Critic:
    def evaluate(self, task: str, answer: str, verified: bool, evidence: list[Any]) -> Reflection:
        strengths=[]; weaknesses=[]
        if verified: strengths.append("objective verification succeeded")
        else: weaknesses.append("objective verification did not succeed")
        if evidence: strengths.append("execution evidence exists")
        else: weaknesses.append("no execution evidence")
        if not answer.strip(): weaknesses.append("empty answer")
        score=(0.6 if verified else 0.0)+(0.2 if evidence else 0.0)+(0.2 if answer.strip() else 0.0)
        next_step="store verified experience" if score>=0.8 else "diagnose failure and retry"
        return Reflection(score>=0.8,round(score,3),strengths,weaknesses,next_step)

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .teacher import TeacherLoop

@dataclass
class CurriculumRun:
    topic: str
    questions: list[str]
    results: list[dict[str, Any]]
    verified: int
    total: int

class AutonomousCurriculum:
    def __init__(self, teacher: TeacherLoop):
        self.teacher = teacher

    async def run(self, topic: str, count: int = 5, session_id: str = "curriculum") -> CurriculumRun:
        questions = await self.teacher.generate_questions(topic, count)
        results = []
        verified = 0
        for question in questions:
            result = await self.teacher.ask(question, session_id=session_id, remember=True)
            verified += int(result.verified)
            results.append({
                "question": result.question,
                "answer": result.answer,
                "verified": result.verified,
                "confidence": result.confidence,
            })
        return CurriculumRun(topic, questions, results, verified, len(results))

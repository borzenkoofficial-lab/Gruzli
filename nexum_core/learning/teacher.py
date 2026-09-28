from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from ..memory.conversation import LearningMemory
from ..model.terminal import OllamaTerminalSession

@dataclass
class LearningResult:
    question: str
    answer: str
    recalled: list[dict[str, Any]]
    memory_item: dict[str, Any] | None
    verified: bool

class TeacherLoop:
    def __init__(self, memory: LearningMemory, teacher: OllamaTerminalSession | None = None):
        self.memory = memory
        self.teacher = teacher or OllamaTerminalSession()

    async def ask(self, question: str, *, session_id: str = "teacher",
                  remember: bool = True, source: str | None = None) -> LearningResult:
        recalled = self.memory.recall(question, limit=8)
        context = "\n".join(item.get("text", "") for item in recalled)
        system = (
            "You are a teacher for Nexum AI Core. Give precise actionable technical knowledge. "
            "Separate facts from assumptions. If uncertain, say so. Never claim verification you did not perform. "
            f"Relevant prior memory:\n{context}"
        )
        answer = await self.teacher.chat(question, system=system)
        item = None
        if remember and answer.strip():
            item = self.memory.remember(
                f"Question: {question}\nAnswer: {answer}",
                source=source or f"ollama:{self.teacher.model}",
                kind="teacher_lesson", session_id=session_id, confidence=0.6
            )
        return LearningResult(question, answer, recalled, item, False)

    async def teach(self, questions: list[str], *, session_id: str = "teacher") -> list[LearningResult]:
        results = []
        for question in questions:
            results.append(await self.ask(question, session_id=session_id))
        return results

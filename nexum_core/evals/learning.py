from __future__ import annotations
from typing import Any
from ..learning.teacher import TeacherLoop
from ..memory.conversation import LearningMemory
from ..memory.store import MemoryStore

class FakeTeacher:
    model = "fake"
    async def chat(self, prompt: str, system: str = "") -> str:
        return "NEXUM_VERIFIED_LESSON: " + prompt

async def run_learning_evals() -> list[dict[str, Any]]:
    memory = LearningMemory(MemoryStore("data/eval-learning.jsonl"))
    loop = TeacherLoop(memory, FakeTeacher())
    result = await loop.ask("How should an agent verify work?", session_id="eval")
    return [{
        "id": "teacher_memory",
        "ok": result.verified and result.memory_item is not None and bool(memory.recall("agent verify work")),
        "details": {"confidence": result.confidence},
    }]

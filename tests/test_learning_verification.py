import asyncio
from nexum_core.learning.verification import verify_lesson
from nexum_core.learning.teacher import TeacherLoop
from nexum_core.memory.conversation import LearningMemory
from nexum_core.memory.store import MemoryStore

class FakeTeacher:
    model = "fake:qwen"
    async def chat(self, prompt, system=""):
        return "This is a substantive verified technical lesson explaining the requested engineering concept in practical detail."

def test_lesson_verification():
    assert verify_lesson("short").ok is False
    assert verify_lesson("This answer contains enough substantive technical information to pass the lesson quality gate.").ok

def test_teacher_only_remembers_verified_lessons(tmp_path):
    async def run():
        memory = LearningMemory(MemoryStore(str(tmp_path / "memory.jsonl")))
        result = await TeacherLoop(memory, FakeTeacher()).ask("Explain agents", session_id="s")
        assert result.verified
        assert result.memory_item is not None
    asyncio.run(run())

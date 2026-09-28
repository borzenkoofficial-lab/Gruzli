from __future__ import annotations
import asyncio
from pathlib import Path
from nexum_core.memory.conversation import LearningMemory
from nexum_core.memory.store import MemoryStore
from nexum_core.learning.teacher import TeacherLoop
from nexum_core.model.terminal import OllamaTerminalSession

class FakeTeacher(OllamaTerminalSession):
    def __init__(self):
        super().__init__(model="fake:qwen")
    async def chat(self, prompt: str, system: str = "") -> str:
        return f"TEACHER_OK: {prompt}"

def test_learning_memory_persists(tmp_path: Path):
    store = MemoryStore(str(tmp_path / "memory.jsonl"))
    memory = LearningMemory(store)
    item = memory.remember("Nexum uses verified trajectories.", source="test", session_id="s1")
    assert item["metadata"]["source"] == "test"
    assert "verified trajectories" in memory.recall("verified trajectories")[0]["text"]

def test_teacher_loop_saves_lesson(tmp_path: Path):
    async def run():
        memory = LearningMemory(MemoryStore(str(tmp_path / "memory.jsonl")))
        result = await TeacherLoop(memory, FakeTeacher()).ask("How do agents verify work?", session_id="s1")
        assert "TEACHER_OK" in result.answer
        assert result.memory_item is not None
        assert memory.recall("agents verify work")
    asyncio.run(run())

def test_ollama_stream_contract():
    assert hasattr(OllamaTerminalSession, "stream")

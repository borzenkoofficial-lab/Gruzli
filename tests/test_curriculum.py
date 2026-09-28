import asyncio
from nexum_core.learning.curriculum import AutonomousCurriculum

class FakeTeacher:
    async def generate_questions(self, topic, count=5):
        return [f"{topic} question {i}" for i in range(count)]
    async def ask(self, question, session_id="curriculum", remember=True):
        class R: pass
        r = R()
        r.question, r.answer, r.verified, r.confidence = question, "A verified technical answer with enough detail.", True, 0.9
        return r

def test_autonomous_curriculum():
    async def run():
        result = await AutonomousCurriculum(FakeTeacher()).run("agents", 3)
        assert result.total == 3
        assert result.verified == 3
    asyncio.run(run())

import asyncio
from nexum_core.learning.curriculum import AutonomousCurriculum

class FakeTeacher:
    async def generate_questions(self, topic, count=5):
        return [f"{topic} {i}" for i in range(count)]
    async def ask(self, question, session_id="x", remember=True):
        class Result: pass
        r = Result()
        r.question = question
        r.answer = "A sufficiently detailed technical lesson with practical implementation guidance."
        r.verified = True
        r.confidence = 0.85
        return r

def test_curriculum_returns_verified_results():
    async def run():
        result = await AutonomousCurriculum(FakeTeacher()).run("tool runtime", 4)
        assert result.verified == 4
        assert all(item["confidence"] >= 0.7 for item in result.results)
    asyncio.run(run())

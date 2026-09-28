from nexum_core.learning.curriculum import AutonomousCurriculum

class FakeTeacher:
    async def generate_questions(self, topic, count=5):
        return [f"{topic} question {i}" for i in range(count)]

    async def ask(self, question, session_id="curriculum", remember=True):
        class R:
            pass
        r = R()
        r.question = question
        r.answer = "A verified technical answer with enough detail."
        r.verified = True
        r.confidence = 0.9
        return r

import pytest

@pytest.mark.asyncio
async def test_autonomous_curriculum():
    run = await AutonomousCurriculum(FakeTeacher()).run("agents", 3)
    assert run.total == 3
    assert run.verified == 3

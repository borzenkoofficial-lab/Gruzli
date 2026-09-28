import pytest

from nexum_core.reasoning.development import CouncilDevelopmentOrchestrator


class FakeCouncilResult:
    def __init__(self, answer):
        self.members = [{"role": "architect"}]
        self.critiques = [{"role": "critic"}]
        self.final = {"answer": answer}


class FakeCouncil:
    def __init__(self):
        self.calls = 0

    async def deliberate(self, task, providers, **kwargs):
        self.calls += 1
        return FakeCouncilResult(
            "repair plan" if self.calls > 1 else "initial executable plan"
        )


class FakeLoop:
    def __init__(self):
        self.calls = 0

    async def run(self, task, context, **kwargs):
        self.calls += 1
        return {
            "run_id": f"run-{self.calls}",
            "verified": self.calls >= 2,
            "answer": "ok" if self.calls >= 2 else "failed",
            "events": [
                {"kind": "verification", "ok": self.calls >= 2, "errors": [] if self.calls >= 2 else ["build failed"]}
            ],
        }


@pytest.mark.asyncio
async def test_council_development_repairs_until_verified():
    council = FakeCouncil()
    loop = FakeLoop()
    runner = CouncilDevelopmentOrchestrator(council, loop, max_rounds=2)

    result = await runner.run("build app", ["mock"], judge="mock")

    assert result.verified is True
    assert result.rounds == 2
    assert len(result.repairs) == 1
    assert council.calls == 2
    assert loop.calls == 2

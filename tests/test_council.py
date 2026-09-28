from nexum_core.reasoning.council import AICouncil


async def _generate(provider: str, prompt: str, max_tokens: int):
    return {"provider": provider, "model": provider, "answer": prompt}


async def test_council_has_independent_and_critique_phases():
    result = await AICouncil(_generate).deliberate("build an app", ["mock"], judge="mock")
    assert len(result.members) == 4
    assert len(result.critiques) == 4
    assert result.final is not None


async def test_council_rejects_empty_provider_list():
    try:
        await AICouncil(_generate).deliberate("task", [])
    except ValueError:
        return
    assert False, "expected ValueError"

from nexum_core.reasoning.council import AICouncil


async def generate(provider: str, prompt: str, max_tokens: int):
    return {"provider": provider, "model": provider, "answer": prompt}


async def verify(task: str, answer: str):
    return {"ok": bool(answer.strip()), "checks": [{"type": "answer_presence", "ok": bool(answer.strip())}], "evidence": [], "issues": []}


async def test_council_verification_hook():
    result = await AICouncil(generate, verify=verify).deliberate(
        "build an app", ["mock"], judge="mock", verify=True
    )
    assert len(result.members) == 4
    assert len(result.critiques) == 4
    assert result.final is not None
    assert result.verified is True
    assert result.verification["ok"] is True


async def test_council_rejects_empty_provider_list():
    try:
        await AICouncil(generate).deliberate("task", [])
    except ValueError:
        return
    assert False, "expected ValueError"

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class CouncilMember:
    role: str
    provider: str
    instruction: str


@dataclass
class CouncilResult:
    task: str
    members: list[dict[str, Any]] = field(default_factory=list)
    critiques: list[dict[str, Any]] = field(default_factory=list)
    final: dict[str, Any] | None = None
    verified: bool = False


class AICouncil:
    """Structured multi-model deliberation: independent work -> critique -> synthesis."""

    DEFAULT_ROLES = (
        ("architect", "Design the solution, identify constraints, interfaces, risks and a minimal executable plan."),
        ("researcher", "Analyze facts, assumptions, alternatives and missing evidence. Flag uncertainty explicitly."),
        ("coder", "Translate the task into concrete implementation steps, code-level decisions and verification criteria."),
        ("critic", "Look for contradictions, unsafe assumptions, regressions and failure modes."),
    )

    def __init__(self, generate: Callable[[str, str, str], Awaitable[dict[str, Any]]]):
        self.generate = generate

    async def deliberate(
        self,
        task: str,
        providers: list[str],
        judge: str | None = None,
        context: str = "",
        max_tokens: int = 1200,
    ) -> CouncilResult:
        if not providers:
            raise ValueError("At least one provider is required")

        members = [
            CouncilMember(role=role, provider=providers[i % len(providers)], instruction=instruction)
            for i, (role, instruction) in enumerate(self.DEFAULT_ROLES)
        ]
        independent: list[dict[str, Any]] = []
        for member in members:
            prompt = (
                f"You are the {member.role} member of Nexum AI Council. "
                "Do not reveal hidden chain-of-thought. Return concise, structured conclusions.\n\n"
                f"Role: {member.instruction}\nTask:\n{task}\nContext:\n{context}"
            )
            result = await self.generate(member.provider, prompt, max_tokens)
            independent.append({"role": member.role, **result})

        critique_input = "\n\n".join(
            f"=== {item['role']} / {item['provider']} ===\n{item['answer']}" for item in independent
        )
        critiques: list[dict[str, Any]] = []
        for member in members:
            prompt = (
                f"You are the {member.role} critic in an AI council. "
                "Review the candidate work below. Identify concrete conflicts, unsupported assumptions, "
                "missing steps and the evidence needed to resolve them. Do not reveal hidden chain-of-thought.\n\n"
                f"Original task:\n{task}\n\nCandidates:\n{critique_input}"
            )
            result = await self.generate(member.provider, prompt, max_tokens)
            critiques.append({"role": member.role, **result})

        final: dict[str, Any] | None = None
        if judge:
            evidence = critique_input + "\n\n=== CRITIQUES ===\n" + "\n\n".join(
                f"=== {item['role']} / {item['provider']} ===\n{item['answer']}" for item in critiques
            )
            prompt = (
                "You are the final judge of Nexum AI Council. Synthesize the strongest answer from the "
                "candidate work and critiques. Resolve conflicts using explicit evidence and constraints. "
                "Do not reveal hidden chain-of-thought. Return only the final actionable answer.\n\n"
                f"Original task:\n{task}\n\nCouncil record:\n{evidence}"
            )
            final = await self.generate(judge, prompt, max_tokens)

        return CouncilResult(task=task, members=independent, critiques=critiques, final=final, verified=False)

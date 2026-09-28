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
    verification: dict[str, Any] = field(default_factory=dict)


class AICouncil:
    """Multi-model deliberation with bounded execution and evidence-based verification."""

    DEFAULT_ROLES = (
        ("architect", "Design the solution, constraints, interfaces, risks and minimal executable plan."),
        ("researcher", "Analyze facts, assumptions, alternatives and missing evidence. Flag uncertainty."),
        ("coder", "Translate the task into concrete implementation and verification criteria."),
        ("critic", "Find contradictions, unsafe assumptions, regressions and failure modes."),
    )

    def __init__(
        self,
        generate: Callable[[str, str, int], Awaitable[dict[str, Any]]],
        verify: Callable[[str, str], Awaitable[dict[str, Any]]] | None = None,
    ):
        self.generate = generate
        self.verify = verify

    async def deliberate(
        self,
        task: str,
        providers: list[str],
        judge: str | None = None,
        context: str = "",
        max_tokens: int = 1200,
        verify: bool = True,
    ) -> CouncilResult:
        if not providers:
            raise ValueError("At least one provider is required")

        members = [
            CouncilMember(role=r, provider=providers[i % len(providers)], instruction=instruction)
            for i, (r, instruction) in enumerate(self.DEFAULT_ROLES)
        ]

        independent = []
        for member in members:
            prompt = (
                f"You are the {member.role} member of Nexum AI Council. "
                "Return concise conclusions, not hidden chain-of-thought.\n\n"
                f"Role: {member.instruction}\nTask:\n{task}\nContext:\n{context}"
            )
            result = await self.generate(member.provider, prompt, max_tokens)
            independent.append({"role": member.role, **result})

        candidates = "\n\n".join(
            f"=== {x['role']} / {x['provider']} ===\n{x['answer']}" for x in independent
        )
        critiques = []
        for member in members:
            prompt = (
                "Review the candidate work below. Identify concrete conflicts, unsupported assumptions, "
                "missing steps and evidence required to resolve them. Do not reveal hidden chain-of-thought.\n\n"
                f"Original task:\n{task}\n\nCandidates:\n{candidates}"
            )
            result = await self.generate(member.provider, prompt, max_tokens)
            critiques.append({"role": member.role, **result})

        final = None
        if judge:
            record = candidates + "\n\n=== CRITIQUES ===\n" + "\n\n".join(
                f"=== {x['role']} / {x['provider']} ===\n{x['answer']}" for x in critiques
            )
            prompt = (
                "Synthesize the final actionable answer from the candidate work and critiques. "
                "Resolve conflicts using explicit evidence and constraints. Do not reveal hidden chain-of-thought.\n\n"
                f"Original task:\n{task}\n\nCouncil record:\n{record}"
            )
            final = await self.generate(judge, prompt, max_tokens)

        verification = {"ok": False, "checks": [], "evidence": []}
        if verify and final and self.verify:
            verification = await self.verify(task, final.get("answer", ""))

        return CouncilResult(
            task=task,
            members=independent,
            critiques=critiques,
            final=final,
            verified=bool(verification.get("ok")),
            verification=verification,
        )

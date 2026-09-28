from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .council import AICouncil
from .loop import AgentLoop


@dataclass
class DevelopmentResult:
    task: str
    run_id: str | None = None
    verified: bool = False
    rounds: int = 0
    plan: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)
    repairs: list[dict[str, Any]] = field(default_factory=list)


class CouncilDevelopmentOrchestrator:
    """Council -> execution -> evidence -> bounded repair -> verification.

    The council never mutates the workspace. AgentLoop/ToolExecutor remain the
    single mutation boundary, while ProjectRuntime/Verifier provide evidence.
    """

    def __init__(
        self,
        council: AICouncil,
        agent_loop: AgentLoop,
        max_rounds: int = 2,
    ):
        self.council = council
        self.agent_loop = agent_loop
        self.max_rounds = max(1, max_rounds)

    @staticmethod
    def _final_answer(result) -> str:
        return str((result.final or {}).get("answer", ""))

    @staticmethod
    def _compact_events(result: dict[str, Any], limit: int = 12) -> str:
        events = result.get("events", [])[-limit:]
        lines: list[str] = []
        for event in events:
            kind = event.get("kind", "event")
            if kind in {"tool_result", "verification", "repair", "repair_plan", "action_requested"}:
                lines.append(f"{kind}: {event}")
        return "\n".join(lines)

    async def run(
        self,
        task: str,
        providers: list[str],
        judge: str | None = None,
        context: str = "",
        preferred_provider: str | None = None,
        max_tokens: int = 1200,
        cancel_check=None,
        event_sink=None,
    ) -> DevelopmentResult:
        if not providers:
            raise ValueError("At least one provider is required")

        def emit(kind: str, **payload):
            if event_sink:
                event_sink({"kind": kind, **payload})

        emit("council_start", task=task, providers=providers, judge=judge)
        council = await self.council.deliberate(
            task,
            providers,
            judge=judge,
            context=context,
            max_tokens=max_tokens,
            verify=False,
        )
        plan = {
            "members": council.members,
            "critiques": council.critiques,
            "final": council.final,
        }
        emit("council_member", count=len(council.members))
        emit("council_critique", count=len(council.critiques))
        emit("council_judge", answer=self._final_answer(council)[:12000])

        council_context = (
            "NEXUM COUNCIL PLAN. Treat this as planning input, not proof of completion.\n"
            f"{self._final_answer(council)}\n"
            "You must inspect the workspace, execute changes through registered tools, "
            "and verify the result with objective evidence before finalizing."
        )

        execution = await self.agent_loop.run(
            task,
            f"{context}\n\n{council_context}",
            cancel_check=cancel_check,
            event_sink=event_sink,
            preferred_provider=preferred_provider,
            council_context=plan,
        )
        repairs: list[dict[str, Any]] = []

        for round_no in range(1, self.max_rounds):
            if execution.get("verified"):
                break
            evidence = self._compact_events(execution)
            emit("repair_round", round=round_no, evidence=evidence)
            repair_council = await self.council.deliberate(
                task,
                providers,
                judge=judge,
                context=(
                    f"{context}\nPrevious execution was not verified.\n"
                    f"Observed execution evidence:\n{evidence}\n"
                    "Produce a concrete repair plan: what to inspect, what to change, "
                    "and what build/test/verification evidence must pass."
                ),
                max_tokens=max_tokens,
                verify=False,
            )
            repair_answer = self._final_answer(repair_council)
            repair = {
                "round": round_no,
                "members": repair_council.members,
                "critiques": repair_council.critiques,
                "final": repair_council.final,
                "evidence": evidence,
            }
            repairs.append(repair)
            emit("council_judge", round=round_no, answer=repair_answer[:12000])

            execution = await self.agent_loop.run(
                task,
                (
                    f"{context}\n\n"
                    f"Previous execution evidence:\n{evidence}\n\n"
                    "COUNCIL REPAIR PLAN:\n"
                    f"{repair_answer}\n\n"
                    "Apply the repair through tools, then rerun build/test/verification. "
                    "Do not claim completion without evidence."
                ),
                cancel_check=cancel_check,
                event_sink=event_sink,
                preferred_provider=preferred_provider,
                council_context=repair,
            )

        emit(
            "execution_complete",
            verified=bool(execution.get("verified")),
            run_id=execution.get("run_id"),
            rounds=len(repairs) + 1,
        )
        return DevelopmentResult(
            task=task,
            run_id=execution.get("run_id"),
            verified=bool(execution.get("verified")),
            rounds=len(repairs) + 1,
            plan=plan,
            execution=execution,
            repairs=repairs,
        )

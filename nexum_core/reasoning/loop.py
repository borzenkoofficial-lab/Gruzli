from dataclasses import dataclass
from ..model.types import GenerationRequest, Message
from ..model.router import ModelRouter
from .state import ExecutionState
from .planner import Planner
from .verifier import Verifier
from ..training.trajectory import Trajectory
from ..training.collector import TrajectoryCollector

@dataclass
class AgentLoop:
    router: ModelRouter
    max_iterations: int = 8

    async def run(self, task: str, context: str = "", agents: list[str] | None = None) -> dict:
        agents = agents or []
        state = ExecutionState(task=task)
        plan = Planner().build(task, agents)
        trajectory = Trajectory(task=task, metadata={"agents": agents, "plan": [s.__dict__ for s in plan.steps]})
        messages = [
            Message("system", "You are Nexum AI Core. Plan, act, observe, verify. Never claim unobserved actions."),
            Message("user", f"Task:\n{task}\n\nContext:\n{context}\n\nPlan:\n{plan.objective}")
        ]
        for i in range(self.max_iterations):
            state.iteration = i + 1
            result = await self.router.generate(GenerationRequest(messages=messages, max_tokens=2048))
            state.event("model_output", iteration=i + 1, model=result.model, content=result.content)
            trajectory.record("message", {"role":"assistant","content":result.content,"iteration":i+1})
            messages.append(Message("assistant", result.content))
            if result.content.strip().lower().startswith("final:"):
                verification = Verifier().verify([result.content], "model produced final response")
                state.phase = "completed"
                state.verified = verification.ok
                trajectory.verification = verification.__dict__
                trajectory.success = verification.ok
                break
            messages.append(Message("user", "Continue only if work remains. Verify the previous step and produce the next concrete step."))
        if not trajectory.verification:
            trajectory.verification = {"ok": False, "evidence": [], "errors": ["Run ended without explicit FINAL:"]}
        TrajectoryCollector("data/memory/trajectories.jsonl").append(trajectory)
        return {"answer": state.events[-1]["content"] if state.events else "", "iterations": state.iteration, "verified": state.verified, "events": state.events, "plan": plan.objective}

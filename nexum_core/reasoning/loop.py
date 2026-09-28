from dataclasses import dataclass
from ..model.types import GenerationRequest, Message
from ..model.router import ModelRouter
from .state import ExecutionState

@dataclass
class AgentLoop:
    router: ModelRouter
    max_iterations: int = 8

    async def run(self, task: str, context: str = "") -> dict:
        state = ExecutionState(task=task)
        messages = [
            Message("system", "You are Nexum AI Core. Plan, act, observe, verify. Never claim unobserved actions."),
            Message("user", f"Task:\n{task}\n\nContext:\n{context}")
        ]
        for i in range(self.max_iterations):
            state.iteration = i + 1
            result = await self.router.generate(GenerationRequest(messages=messages, max_tokens=2048))
            state.event("model_output", iteration=i + 1, model=result.model, content=result.content)
            messages.append(Message("assistant", result.content))
            if result.content.strip().lower().startswith("final:"):
                state.phase = "completed"
                state.verified = True
                break
            messages.append(Message("user", "Review the previous step. If work remains, produce the next concrete action; otherwise finish with FINAL:."))
        last = state.events[-1]["content"] if state.events else ""
        return {"answer": last, "iterations": state.iteration, "verified": state.verified, "events": state.events}

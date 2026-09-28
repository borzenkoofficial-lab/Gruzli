from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from ..model.types import GenerationRequest, Message
from ..model.router import ModelRouter

@dataclass
class AgentLoop:
    router: ModelRouter
    max_iterations: int = 8
    seen_actions: set[str] = field(default_factory=set)

    async def run(self, task: str, context: str = "") -> dict[str, Any]:
        messages = [
            Message("system", "You are Nexum AI Core. Plan, act, verify, and correct. Do not claim actions you did not perform."),
            Message("user", f"Task:\n{task}\n\nContext:\n{context}")
        ]
        trace = []
        for i in range(self.max_iterations):
            result = await self.router.generate(GenerationRequest(messages=messages, max_tokens=2048))
            trace.append({"iteration": i + 1, "response": result.content})
            messages.append(Message("assistant", result.content))
            if result.content.strip().lower().startswith("final:"):
                break
            messages.append(Message("user", "Continue only if work remains. Verify the previous step and produce the next concrete step."))
        return {"answer": trace[-1]["response"] if trace else "", "iterations": len(trace), "trace": trace}

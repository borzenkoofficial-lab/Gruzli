from dataclasses import dataclass
from ..model.types import GenerationRequest, Message
from ..model.router import ModelRouter
from ..tools.executor import ToolExecutor, ToolCall
from ..agents.protocol import parse_decision, ProtocolError
from ..training.trajectory import Trajectory
from ..training.collector import TrajectoryCollector
from .state import ExecutionState
from .policy import SYSTEM_POLICY
from .planner import Planner
from .verifier import Verifier
from .self_correction import classify_failure, repair_instruction
from .retry import RetryBudget


@dataclass
class AgentLoop:
    router: ModelRouter
    executor: ToolExecutor | None = None
    max_iterations: int = 12
    max_retries: int = 3
    trajectory_path: str = "data/memory/trajectories.jsonl"

    async def run(self, task: str, context: str = "", agents: list[str] | None = None) -> dict:
        state = ExecutionState(task=task)
        trajectory = Trajectory(task=task, run_id=state.run_id, metadata={"agents": agents or []})
        planner = Planner()
        verifier = Verifier()
        retry = RetryBudget(self.max_retries)
        registry = self.executor.registry if self.executor else None
        tool_names = registry.names() if registry else []
        plan = planner.build(task, agents or [], tool_names)
        state.event("plan", objective=plan.objective, steps=[step.__dict__ for step in plan.steps])
        messages = [
            Message("system", SYSTEM_POLICY),
            Message("user", f"Task:\n{task}\nContext:\n{context}\nAgents: {agents or []}\nPlan: {[s.__dict__ for s in plan.steps]}\nTools: {registry.prompt_schemas() if registry else '[]'}"),
        ]
        trajectory.record("message", {"role": "system", "content": SYSTEM_POLICY})

        seen: set[tuple[str, str]] = set()
        outputs: list[object] = []
        last_condition = "Observable evidence confirms completion."

        for i in range(self.max_iterations):
            state.iteration = i + 1
            try:
                result = await self.router.generate(
                    GenerationRequest(messages=messages, max_tokens=2048, temperature=0.2)
                )
                state.event("model_output", iteration=i + 1, model=result.model, content=result.content)
                trajectory.record("message", {"role": "model", "content": result.content, "iteration": i + 1})
                decision = parse_decision(result.content)
            except ProtocolError as exc:
                failure = classify_failure(str(exc))
                if not retry.consume(failure.category, failure.message):
                    state.errors.append(str(exc))
                    break
                state.errors.append(str(exc))
                state.event("repair", category=failure.category, instruction=repair_instruction(failure))
                messages.append(Message("user", repair_instruction(failure)))
                continue

            if decision.kind == "final":
                verification = verifier.verify(outputs, last_condition)
                state.event(
                    "verification",
                    ok=verification.ok,
                    evidence=verification.evidence,
                    errors=verification.errors,
                    checks=verification.checks,
                )
                trajectory.record("verification", {
                    "ok": verification.ok,
                    "evidence": verification.evidence,
                    "errors": verification.errors,
                    "checks": verification.checks,
                })
                if verification.ok:
                    state.phase = "completed"
                    state.verified = True
                    trajectory.success = True
                    TrajectoryCollector(self.trajectory_path).append(trajectory)
                    return {
                        "run_id": state.run_id,
                        "answer": decision.content,
                        "iterations": state.iteration,
                        "verified": True,
                        "events": state.events,
                    }

                failure = classify_failure(None, verification.errors)
                if not retry.consume(failure.category, failure.message):
                    break
                state.event("repair", category=failure.category, instruction=repair_instruction(failure))
                messages.append(Message("user", repair_instruction(failure)))
                continue

            if decision.kind == "actions" and self.executor:
                executed = False
                for action in decision.actions:
                    key = (action.tool, repr(sorted(action.arguments.items())))
                    if key in seen:
                        state.event("action_skipped_duplicate", id=action.id, tool=action.tool)
                        continue
                    seen.add(key)
                    executed = True
                    last_condition = action.success_condition or last_condition
                    state.event("action_requested", id=action.id, tool=action.tool, arguments=action.arguments)
                    trajectory.record("action", {
                        "id": action.id,
                        "tool": action.tool,
                        "arguments": action.arguments,
                        "purpose": action.purpose,
                        "success_condition": action.success_condition,
                    })
                    try:
                        registry.validate_arguments(action.tool, action.arguments)
                        tool_result = self.executor.execute(ToolCall(action.tool, action.arguments))
                    except Exception as exc:
                        tool_result = None
                        error = f"{type(exc).__name__}: {exc}"
                        state.errors.append(error)
                        state.event("tool_result", id=action.id, tool=action.tool, ok=False, error=error)
                        trajectory.record("observation", {"action_id": action.id, "ok": False, "error": error})
                        failure = classify_failure(error)
                        if retry.consume(failure.category, failure.message):
                            messages.append(Message("user", repair_instruction(failure)))
                        continue

                    state.event(
                        "tool_result",
                        id=action.id,
                        tool=action.tool,
                        ok=tool_result.ok,
                        output=tool_result.output,
                        error=tool_result.error,
                    )
                    trajectory.record("observation", {
                        "action_id": action.id,
                        "ok": tool_result.ok,
                        "output": tool_result.output,
                        "error": tool_result.error,
                    })
                    if tool_result.ok:
                        outputs.append(tool_result.output)
                    else:
                        error = tool_result.error or "tool failed"
                        state.errors.append(error)
                        failure = classify_failure(error)
                        if retry.consume(failure.category, failure.message):
                            state.event("repair", category=failure.category, instruction=repair_instruction(failure))
                            messages.append(Message("user", repair_instruction(failure)))
                            continue
                    messages.append(Message(
                        "user",
                        f"Observation for {action.tool}: ok={tool_result.ok}; output={tool_result.output}; error={tool_result.error}",
                    ))
                if not executed:
                    messages.append(Message("user", "All proposed actions were duplicates. Inspect current state and choose a new action."))
            else:
                messages.append(Message("user", "Return valid JSON with registered actions, or final only after verification."))

        state.phase = "failed"
        trajectory.success = False
        trajectory.record("verification", {
            "ok": False,
            "evidence": outputs,
            "errors": state.errors or ["Execution budget exhausted"],
        })
        trajectory.metadata["retry_budget"] = {
            "max_retries": retry.max_retries,
            "used": retry.used,
            "failures": retry.failures,
        }
        TrajectoryCollector(self.trajectory_path).append(trajectory)
        return {
            "run_id": state.run_id,
            "answer": "Execution budget exhausted without verified completion.",
            "iterations": state.iteration,
            "verified": False,
            "events": state.events,
        }

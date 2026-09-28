from dataclasses import dataclass
from typing import Callable
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
from ..projects.repair_loop import RepairPlanner
from .world_model import WorldModel
from .critic import Critic
from .long_horizon import LongHorizonPlanner


@dataclass
class AgentLoop:
    router: ModelRouter
    executor: ToolExecutor | None = None
    max_iterations: int = 12
    max_retries: int = 3
    trajectory_path: str = "data/memory/trajectories.jsonl"

    async def run(
        self,
        task: str,
        context: str = "",
        agents: list[str] | None = None,
        cancel_check: Callable[[], bool] | None = None,
        event_sink: Callable[[dict], None] | None = None,
        preferred_provider: str | None = None,
        council_context: dict | None = None,
    ) -> dict:
        state = ExecutionState(task=task)
        trajectory = Trajectory(task=task, run_id=state.run_id, metadata={"agents": agents or []})
        if council_context:
            trajectory.record("council", council_context)
        planner = Planner()
        verifier = Verifier()
        repair_planner = RepairPlanner()
        world_model = WorldModel()
        critic = Critic()
        horizon = LongHorizonPlanner().create(task)
        emit_bootstrap = True
        retry = RetryBudget(self.max_retries)
        registry = self.executor.registry if self.executor else None
        tool_names = registry.names() if registry else []
        plan = planner.build(task, agents or [], tool_names)

        def emit(kind: str, **data):
            state.event(kind, **data)
            if event_sink:
                event_sink(state.events[-1])

        emit("plan", objective=plan.objective, steps=[step.__dict__ for step in plan.steps], long_horizon=horizon.__dict__)
        world_model.observe(f"Active task: {task}", evidence=f"run:{state.run_id}", confidence=0.4)
        messages = [
            Message("system", SYSTEM_POLICY),
            Message("user", f"Task:\n{task}\nContext:\n{context}\nAgents: {agents or []}\nPlan: {[s.__dict__ for s in plan.steps]}\nTools: {registry.prompt_schemas() if registry else '[]'}"),
        ]
        trajectory.record("message", {"role": "system", "content": SYSTEM_POLICY})
        trajectory.record("message", {"role": "user", "content": task, "context": context})

        seen: set[tuple[str, str]] = set()
        outputs: list[object] = []
        last_condition = "Observable evidence confirms completion."

        for i in range(self.max_iterations):
            if cancel_check and cancel_check():
                emit("run_cancelled")
                return {"run_id": state.run_id, "answer": "Run cancelled.", "iterations": state.iteration, "verified": False, "cancelled": True, "events": state.events}

            state.iteration = i + 1
            state.phase = "reasoning"
            try:
                result = await self.router.generate(
                    GenerationRequest(messages=messages, max_tokens=2048, temperature=0.2),
                    preferred=preferred_provider,
                )
                emit("model_output", iteration=i + 1, model=result.model, content=result.content)
                trajectory.record("message", {"role": "model", "content": result.content, "iteration": i + 1})
                decision = parse_decision(result.content)
            except ProtocolError as exc:
                failure = classify_failure(str(exc))
                if not retry.consume(failure.category, failure.message):
                    state.errors.append(str(exc))
                    break
                state.errors.append(str(exc))
                emit("repair", category=failure.category, instruction=repair_instruction(failure))
                messages.append(Message("user", repair_instruction(failure)))
                continue

            if decision.kind == "final":
                state.phase = "verification"
                verification = verifier.verify(outputs, last_condition)
                emit("verification", ok=verification.ok, evidence=verification.evidence, errors=verification.errors, checks=verification.checks)
                trajectory.record("verification", {"ok": verification.ok, "evidence": verification.evidence, "errors": verification.errors, "checks": verification.checks})
                if verification.ok:
                    state.phase = "completed"
                    state.verified = True
                    trajectory.success = True
                    reflection = critic.evaluate(task, decision.content, True, outputs)
                    trajectory.record("metadata", {"reflection": reflection.__dict__, "long_horizon": horizon.__dict__})
                    world_model.observe(f"Completed task: {task}", evidence=f"run:{state.run_id}", confidence=1.0)
                    TrajectoryCollector(self.trajectory_path).append(trajectory)
                    return {"run_id": state.run_id, "answer": decision.content, "iterations": state.iteration, "verified": True, "events": state.events}
                failure = classify_failure(None, verification.errors)
                if not retry.consume(failure.category, failure.message):
                    break
                emit("repair", category=failure.category, instruction=repair_instruction(failure))
                messages.append(Message("user", repair_instruction(failure)))
                continue

            if decision.kind == "actions" and self.executor:
                executed = False
                state.phase = "tool_execution"
                for action in decision.actions:
                    if cancel_check and cancel_check():
                        emit("run_cancelled")
                        return {"run_id": state.run_id, "answer": "Run cancelled.", "iterations": state.iteration, "verified": False, "cancelled": True, "events": state.events}
                    key = (action.tool, repr(sorted(action.arguments.items())))
                    if key in seen:
                        # Verification/repair often needs to rerun the same build/test after a mutation.
                        # Allow a previously failed action to be retried after the model changes state.
                        if not any(e.get("kind") == "repair" for e in state.events[-8:]):
                            emit("action_skipped_duplicate", id=action.id, tool=action.tool)
                            continue
                    seen.add(key)
                    executed = True
                    state.current_step = action.id
                    last_condition = action.success_condition or last_condition
                    emit("action_requested", id=action.id, tool=action.tool, arguments=action.arguments)
                    trajectory.record("action", {"id": action.id, "tool": action.tool, "arguments": action.arguments, "purpose": action.purpose, "success_condition": action.success_condition})
                    try:
                        registry.validate_arguments(action.tool, action.arguments)
                        tool_result = self.executor.execute(ToolCall(action.tool, action.arguments))
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                        state.errors.append(error)
                        emit("tool_result", id=action.id, tool=action.tool, ok=False, error=error)
                        trajectory.record("observation", {"action_id": action.id, "ok": False, "error": error})
                        failure = classify_failure(error)
                        if retry.consume(failure.category, failure.message):
                            emit("repair", category=failure.category, instruction=repair_instruction(failure))
                            messages.append(Message("user", repair_instruction(failure)))
                        continue

                    emit("tool_result", id=action.id, tool=action.tool, ok=tool_result.ok, output=tool_result.output, error=tool_result.error)
                    trajectory.record("observation", {"action_id": action.id, "ok": tool_result.ok, "output": tool_result.output, "error": tool_result.error})
                    if tool_result.ok:
                        outputs.append(tool_result.output)
                        if action.tool == "project_lifecycle" and isinstance(tool_result.output, dict) and tool_result.output.get("ok") is False:
                            details = {"parsed_error": tool_result.output.get("details", {}).get("parsed_error", {})}
                            plan = repair_planner.plan(details)
                            emit("repair_plan", category=plan.category, instruction=plan.instruction, evidence=plan.evidence, file=plan.file, line=plan.line)
                            trajectory.record("repair", {"category": plan.category, "instruction": plan.instruction, "evidence": plan.evidence, "file": plan.file, "line": plan.line})
                            messages.append(Message("user", f"Verification failed. Repair required: {plan.instruction}. Evidence: {plan.evidence}. Inspect affected files, mutate them, then rerun build/test/verify."))
                            continue
                    else:
                        error = tool_result.error or "tool failed"
                        state.errors.append(error)
                        failure = classify_failure(error)
                        if retry.consume(failure.category, failure.message):
                            emit("repair", category=failure.category, instruction=repair_instruction(failure))
                            messages.append(Message("user", repair_instruction(failure)))
                            continue
                    messages.append(Message("user", f"Observation for {action.tool}: ok={tool_result.ok}; output={tool_result.output}; error={tool_result.error}"))
                if not executed:
                    messages.append(Message("user", "All proposed actions were duplicates. Inspect current state and choose a new action."))
            else:
                messages.append(Message("user", "Return valid JSON with registered actions, or final only after verification."))

        state.phase = "failed"
        trajectory.success = False
        reflection = critic.evaluate(task, "Execution budget exhausted", False, outputs)
        trajectory.record("metadata", {"reflection": reflection.__dict__, "long_horizon": horizon.__dict__})
        trajectory.record("verification", {"ok": False, "evidence": outputs, "errors": state.errors or ["Execution budget exhausted"]})
        trajectory.metadata["completion"] = {"verified": False, "phase": state.phase, "iterations": state.iteration}
        trajectory.metadata["retry_budget"] = {"max_retries": retry.max_retries, "used": retry.used, "failures": retry.failures}
        TrajectoryCollector(self.trajectory_path).append(trajectory)
        return {"run_id": state.run_id, "answer": "Execution budget exhausted without verified completion.", "iterations": state.iteration, "verified": False, "events": state.events}

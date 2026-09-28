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

@dataclass
class AgentLoop:
    router: ModelRouter
    executor: ToolExecutor | None = None
    max_iterations: int = 12
    trajectory_path: str = 'data/memory/trajectories.jsonl'

    async def run(self, task: str, context: str = '', agents: list[str] | None = None) -> dict:
        state = ExecutionState(task=task)
        trajectory = Trajectory(task=task, metadata={'agents': agents or []})
        planner = Planner()
        verifier = Verifier()
        registry = self.executor.registry if self.executor else None
        tool_names = registry.names() if registry else []
        plan = planner.build(task, agents or [], tool_names)
        state.event('plan', objective=plan.objective, steps=[step.__dict__ for step in plan.steps])
        messages = [
            Message('system', SYSTEM_POLICY),
            Message('user', f'Task:\n{task}\nContext:\n{context}\nAgents: {agents or []}\nPlan: {[s.__dict__ for s in plan.steps]}\nTools: {registry.prompt_schemas() if registry else "[]"}')
        ]
        trajectory.record('message', {'role': 'system', 'content': SYSTEM_POLICY})
        seen: set[tuple[str, str]] = set()
        outputs: list[object] = []
        last_condition = 'Observable evidence confirms completion.'
        for i in range(self.max_iterations):
            state.iteration = i + 1
            try:
                result = await self.router.generate(GenerationRequest(messages=messages, max_tokens=2048, temperature=0.2))
                state.event('model_output', iteration=i + 1, model=result.model, content=result.content)
                trajectory.record('message', {'role': 'model', 'content': result.content, 'iteration': i + 1})
                decision = parse_decision(result.content)
            except ProtocolError as exc:
                state.errors.append(str(exc))
                messages.append(Message('user', f'Protocol error: {exc}. Return valid JSON only.'))
                continue
            if decision.kind == 'final':
                verification = verifier.verify(outputs, last_condition)
                state.event('verification', ok=verification.ok, evidence=verification.evidence, errors=verification.errors)
                trajectory.record('verification', {'ok': verification.ok, 'evidence': verification.evidence, 'errors': verification.errors})
                if verification.ok:
                    state.phase = 'completed'
                    state.verified = True
                    trajectory.success = True
                    TrajectoryCollector(self.trajectory_path).append(trajectory)
                    return {'answer': decision.content, 'iterations': state.iteration, 'verified': True, 'events': state.events}
                messages.append(Message('user', f'Final rejected. Verification failed: {verification.errors}. Perform another observable action.'))
                continue
            if decision.kind == 'actions' and self.executor:
                executed = False
                for action in decision.actions:
                    key = (action.tool, repr(sorted(action.arguments.items())))
                    if key in seen:
                        state.event('action_skipped_duplicate', id=action.id, tool=action.tool)
                        continue
                    seen.add(key)
                    executed = True
                    last_condition = action.success_condition or last_condition
                    state.event('action_requested', id=action.id, tool=action.tool, arguments=action.arguments)
                    trajectory.record('action', {'id': action.id, 'tool': action.tool, 'arguments': action.arguments, 'purpose': action.purpose, 'success_condition': action.success_condition})
                    try:
                        registry.validate_arguments(action.tool, action.arguments)
                        result = self.executor.execute(ToolCall(action.tool, action.arguments))
                    except Exception as exc:
                        error = f'{type(exc).__name__}: {exc}'
                        state.errors.append(error)
                        state.event('tool_result', id=action.id, tool=action.tool, ok=False, error=error)
                        trajectory.record('observation', {'action_id': action.id, 'ok': False, 'error': error})
                        messages.append(Message('user', f'Tool {action.tool} failed: {error}. Diagnose and choose a different action.'))
                        continue
                    state.event('tool_result', id=action.id, tool=action.tool, ok=result.ok, output=result.output, error=result.error)
                    trajectory.record('observation', {'action_id': action.id, 'ok': result.ok, 'output': result.output, 'error': result.error})
                    if result.ok:
                        outputs.append(result.output)
                    else:
                        state.errors.append(result.error or 'tool failed')
                    messages.append(Message('user', f'Observation for {action.tool}: ok={result.ok}; output={result.output}; error={result.error}'))
                if not executed:
                    messages.append(Message('user', 'All proposed actions were duplicates. Inspect current state and choose a new action.'))
            else:
                messages.append(Message('user', 'Return valid JSON with registered actions, or final only after verification.'))
        state.phase = 'failed'
        trajectory.success = False
        trajectory.record('verification', {'ok': False, 'evidence': outputs, 'errors': state.errors or ['Execution budget exhausted']})
        TrajectoryCollector(self.trajectory_path).append(trajectory)
        return {'answer': 'Execution budget exhausted without verified completion.', 'iterations': state.iteration, 'verified': False, 'events': state.events}

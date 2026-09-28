from dataclasses import dataclass

@dataclass
class PlanStep:
    id: str
    objective: str
    success_condition: str
    tools: list[str]

@dataclass
class Plan:
    objective: str
    steps: list[PlanStep]

class Planner:
    def build(self, task: str, agents: list[str], tool_names: list[str] | None = None) -> Plan:
        text = task.lower()
        available = set(tool_names or [])
        steps = []
        def add(step_id, objective, success, candidates):
            selected = [name for name in candidates if name in available]
            steps.append(PlanStep(step_id, objective, success, selected))
        if any(w in text for w in ('create', 'write', 'edit', 'fix', 'implement')):
            add('inspect', 'Inspect the relevant workspace before changing it.', 'Relevant files and constraints are observable.', ('list_files', 'search_files', 'read_file'))
            add('change', 'Apply the smallest change that addresses the task.', 'The requested file change is observable.', ('write_file',))
            add('verify', 'Inspect the changed result and verify the requested outcome.', 'Observable evidence confirms completion.', ('read_file', 'search_files', 'run_command'))
        elif any(w in text for w in ('build', 'test', 'compile', 'pytest', 'npm test', 'verify')):
            add('inspect', 'Inspect the project and determine the available build/test commands.', 'Project structure and package scripts are observable.', ('list_files', 'read_file', 'search_files'))
            add('build', 'Run the project build or compile check.', 'Build completes successfully with observable output.', ('run_command',))
            add('test', 'Run the project test suite.', 'Tests complete successfully with observable output.', ('run_command',))
        elif any(w in text for w in ('list', 'show', 'find', 'inspect')):
            add('inspect', 'Inspect the workspace for the requested information.', 'The requested information is observable.', ('list_files', 'search_files', 'read_file'))
        else:
            add('execute', task, 'Observable evidence confirms completion.', tuple(available))
        if not steps:
            steps = [PlanStep('step-1', task, 'Observable evidence confirms completion.', [])]
        return Plan(task, steps)

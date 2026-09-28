from dataclasses import dataclass
from ..model.types import GenerationRequest, Message
from ..model.router import ModelRouter
from ..tools.executor import ToolExecutor, ToolCall
from ..agents.protocol import parse_decision
from .state import ExecutionState
from .policy import SYSTEM_POLICY

@dataclass
class AgentLoop:
    router: ModelRouter
    executor: ToolExecutor | None = None
    max_iterations: int = 12

    async def run(self, task: str, context: str = '', agents: list[str] | None = None) -> dict:
        state=ExecutionState(task=task)
        messages=[Message('system',SYSTEM_POLICY), Message('user',f'Task:\n{task}\nContext:\n{context}\nAgents: {agents or []}')]
        for i in range(self.max_iterations):
            state.iteration=i+1
            result=await self.router.generate(GenerationRequest(messages=messages,max_tokens=2048,temperature=0.2))
            state.event('model_output',iteration=i+1,model=result.model,content=result.content)
            decision=parse_decision(result.content)
            if decision.kind=='final':
                state.phase='completed'; state.verified=True
                return {'answer':decision.content,'iterations':state.iteration,'verified':True,'events':state.events}
            if decision.kind=='actions' and self.executor:
                for action in decision.actions:
                    state.event('action_requested',id=action.id,tool=action.tool,arguments=action.arguments)
                    tool_result=self.executor.execute(ToolCall(action.name if hasattr(action,'name') else action.tool, action.arguments))
                    state.event('tool_result',id=action.id,tool=action.tool,ok=tool_result.ok,output=tool_result.output,error=tool_result.error)
                    messages.append(Message('user',f'Tool {action.tool} result: ok={tool_result.ok}; output={tool_result.output}; error={tool_result.error}. Evaluate this result.'))
            else:
                messages.append(Message('user','Convert your next step into a valid JSON action or return a JSON final only after verification.'))
        state.phase='failed'
        return {'answer':'Execution budget exhausted without verified completion.','iterations':state.iteration,'verified':False,'events':state.events}
from .model.router import ModelRouter
from .memory.store import MemoryStore
from .tools.workspace import build_registry
from .tools.code_runner import CodeRunner
from .tools.executor import ToolExecutor
from .reasoning.loop import AgentLoop
from .agents.orchestrator import Orchestrator

class NexumRuntime:
    def __init__(self, workspace='.'):
        self.router=ModelRouter()
        self.memory=MemoryStore()
        self.tools=build_registry(workspace)
        self.tools.register(CodeRunner())
        self.executor=ToolExecutor(self.tools)
        self.orchestrator=Orchestrator()
        self.loop=AgentLoop(self.router,self.executor)

    async def chat(self, task: str, context: str = ''):
        agents=self.orchestrator.select(task)
        return await self.loop.run(task,context,agents)
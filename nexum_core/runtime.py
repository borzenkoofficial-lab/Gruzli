from .model.router import ModelRouter
from .memory.store import MemoryStore
from .tools.workspace import build_registry
from .tools.executor import ToolExecutor
from .reasoning.loop import AgentLoop
from .agents.orchestrator import Orchestrator

class NexumRuntime:
    def __init__(self, workspace="."):
        self.router = ModelRouter()
        self.memory = MemoryStore()
        self.tools = build_registry(workspace)
        self.executor = ToolExecutor(self.tools)
        self.orchestrator = Orchestrator()
        self.loop = AgentLoop(self.router)

    async def chat(self, task: str, context: str = ""):
        result = await self.loop.run(task, context)
        result["agents"] = self.orchestrator.select(task)
        return result

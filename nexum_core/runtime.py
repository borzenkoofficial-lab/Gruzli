from .model.router import ModelRouter
from .memory.store import MemoryStore
from .tools.workspace import build_registry
from .reasoning.loop import AgentLoop

class NexumRuntime:
    def __init__(self, workspace: str = "."):
        self.router = ModelRouter()
        self.memory = MemoryStore()
        self.tools = build_registry(workspace)
        self.loop = AgentLoop(self.router)

    async def chat(self, task: str, context: str = ""):
        return await self.loop.run(task, context)

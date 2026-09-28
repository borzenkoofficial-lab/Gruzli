from .model.router import ModelRouter
from .memory.store import MemoryStore
from .tools.workspace import build_registry
from .tools.code_runner import CodeRunner
from .tools.command_runner import RunCommand
from .tools.executor import ToolExecutor
from .tools.web import WebFetchTool, NetworkPolicy
from .tools.base import Tool
from .tools.git_workspace import GitWorkspaceTool
from .projects.runtime import ProjectRuntime
from .config.settings import settings
from .reasoning.loop import AgentLoop
from .agents.orchestrator import Orchestrator


class ProjectLifecycleTool(Tool):
    name = "project_lifecycle"
    description = "Inspect, install, build, test, or run verification on a project in the workspace."
    parameters = {"type":"object","properties":{"operation":{"type":"string","enum":["inspect","install","build","test","verify"]},"path":{"type":"string","default":"."}},"required":["operation"],"additionalProperties":False}
    def __init__(self, workspace): self.root = workspace
    def execute(self, operation, path="."):
        from pathlib import Path
        root = (Path(self.root) / path).resolve(); root.relative_to(Path(self.root).resolve())
        runtime = ProjectRuntime(str(root))
        if operation == "inspect": return runtime.inspect().__dict__
        if operation == "install": return runtime.install().__dict__
        if operation == "build": return runtime.build().__dict__
        if operation == "test": return runtime.test().__dict__
        if operation == "verify": return runtime.verify_and_repair()
        raise ValueError("unsupported project operation")

class NexumRuntime:
    def __init__(self, workspace="."):
        self.workspace = workspace
        self.router = ModelRouter()
        self.memory = MemoryStore()
        self.tools = build_registry(workspace)
        self.tools.register(CodeRunner())
        self.tools.register(RunCommand(workspace))
        self.tools.register(WebFetchTool(NetworkPolicy(mode=settings.network_mode, max_bytes=settings.network_max_bytes, timeout=settings.network_timeout)))
        self.tools.register(GitWorkspaceTool(workspace))
        self.tools.register(ProjectLifecycleTool(workspace))
        self.executor = ToolExecutor(self.tools)
        self.orchestrator = Orchestrator()
        self.loop = AgentLoop(self.router, self.executor)

    async def chat(self, task: str, context: str = "", cancel_check=None, event_sink=None):
        agents = self.orchestrator.select(task)
        return await self.loop.run(task, context, agents, cancel_check=cancel_check, event_sink=event_sink)

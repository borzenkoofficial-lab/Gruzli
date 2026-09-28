from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..projects.runtime import ProjectRuntime
from ..runtime import NexumRuntime
from ..tools.executor import ToolCall

app = FastAPI(title="Nexum AI Core", version="0.4.0")
runtime = NexumRuntime(".")
project_runtimes: dict[str, ProjectRuntime] = {}


class ChatRequest(BaseModel):
    task: str
    context: str = ""


class MemoryRequest(BaseModel):
    text: str
    kind: str = "fact"


class ToolRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


class ProjectRequest(BaseModel):
    path: str


class PreviewRequest(BaseModel):
    path: str


def get_project(path: str) -> ProjectRuntime:
    root = Path(path).resolve()
    project_runtimes[str(root)] = project_runtimes.get(str(root), ProjectRuntime(str(root)))
    return project_runtimes[str(root)]


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexum-ai-core", "version": "0.4.0"}


@app.get("/agents")
async def agents():
    return {"agents": [a.describe() for a in runtime.orchestrator.agents.values()]}


@app.get("/tools")
async def tools():
    return {"tools": runtime.tools.schemas()}


@app.get("/memory")
async def memory():
    return {"items": runtime.memory.all()}


@app.post("/memory")
async def add_memory(request: MemoryRequest):
    return runtime.memory.add(request.text, request.kind)


@app.post("/tools/execute")
async def execute_tool(request: ToolRequest):
    result = runtime.executor.execute(ToolCall(request.name, request.arguments))
    return {"name": result.name, "ok": result.ok, "output": result.output, "error": result.error}


@app.post("/chat")
async def chat(request: ChatRequest):
    return await runtime.chat(request.task, request.context)


@app.post("/projects/inspect")
async def project_inspect(request: ProjectRequest):
    return get_project(request.path).inspect().__dict__


@app.post("/projects/lifecycle")
async def project_lifecycle(request: ProjectRequest):
    return get_project(request.path).lifecycle(install=True)


@app.post("/projects/preview/start")
async def preview_start(request: PreviewRequest):
    result = get_project(request.path).start_preview()
    return result.__dict__


@app.post("/projects/preview/stop")
async def preview_stop(request: PreviewRequest, pid: int):
    result = get_project(request.path).stop_preview(pid)
    if not result.ok:
        raise HTTPException(status_code=404, detail="Preview process not found")
    return result.__dict__

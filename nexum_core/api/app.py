from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..projects.runtime import ProjectRuntime
from ..reasoning.state import RunManager
from ..runtime import NexumRuntime
from ..tools.executor import ToolCall

app = FastAPI(title="Nexum AI Core", version="0.5.0")
runtime = NexumRuntime(".")
runs = RunManager()
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
    allowed = Path(".").resolve()
    try:
        root.relative_to(allowed)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Project path is outside the AI Core workspace") from exc
    project_runtimes[str(root)] = project_runtimes.get(str(root), ProjectRuntime(str(root)))
    return project_runtimes[str(root)]


def run_view(record) -> dict[str, Any]:
    return {
        "run_id": record.run_id,
        "task": record.task,
        "status": record.status,
        "created_at": record.created_at,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "result": record.result,
        "error": record.error,
        "event_count": len(record.events),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexum-ai-core", "version": "0.5.0"}


@app.get("/agents")
async def agents():
    return {"agents": [a.describe() for a in runtime.orchestrator.agents.values()]}


@app.get("/tools")
async def tools():
    return {"tools": runtime.tools.schemas()}


@app.get("/models")
async def models():
    return {"provider": type(runtime.router.provider).__name__}


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
    record = runs.create(request.task)
    task = asyncio.create_task(
        runs.start(record.run_id, lambda: runtime.chat(request.task, request.context))
    )
    runs.attach(record.run_id, task)
    try:
        await task
    except asyncio.CancelledError:
        pass
    return run_view(runs.get(record.run_id))


@app.post("/runs")
async def create_run(request: ChatRequest):
    record = runs.create(request.task)
    task = asyncio.create_task(
        runs.start(record.run_id, lambda: runtime.chat(request.task, request.context))
    )
    runs.attach(record.run_id, task)
    return run_view(record)


@app.get("/runs")
async def list_runs():
    return {"runs": [run_view(record) for record in runs.runs.values()]}


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    try:
        return run_view(runs.get(run_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    try:
        ok = runs.cancel(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return {"run_id": run_id, "cancelled": ok, "status": runs.get(run_id).status}


@app.get("/runs/{run_id}/events")
async def run_events(run_id: str):
    try:
        record = runs.get(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    async def stream() -> AsyncIterator[str]:
        sent = 0
        while True:
            record = runs.get(run_id)
            while sent < len(record.events):
                event = record.events[sent]
                sent += 1
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if record.status in runs.TERMINAL and sent >= len(record.events):
                break
            await asyncio.sleep(0.15)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/projects/inspect")
async def project_inspect(request: ProjectRequest):
    return get_project(request.path).inspect().__dict__


@app.post("/projects/lifecycle")
async def project_lifecycle(request: ProjectRequest):
    return get_project(request.path).lifecycle(install=True)


@app.post("/projects/verify-repair")
async def project_verify_repair(request: ProjectRequest):
    return get_project(request.path).verify_and_repair()


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

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..evals.runtime import all_passed, run_runtime_evals
from ..memory.conversation import LearningMemory
from ..model.terminal import OllamaTerminalSession, detect_ollama
from ..projects.runtime import ProjectRuntime
from ..reasoning.state import RunManager
from ..runtime import NexumRuntime
from ..tools.executor import ToolCall

app = FastAPI(title="Nexum AI Core", version="0.6.0")
runtime = NexumRuntime(".")
runs = RunManager()
learning = LearningMemory(runtime.memory)
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


class RestoreRequest(BaseModel):
    path: str
    snapshot_id: str


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
    result = record.result if isinstance(record.result, dict) else None
    return {
        "run_id": record.run_id,
        "task": record.task,
        "status": record.status,
        "phase": record.phase,
        "iteration": record.iteration,
        "created_at": record.created_at,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "result": result,
        "error": record.error,
        "event_count": len(record.events),
    }


def start_run(task: str, context: str = ""):
    record = runs.create(task)

    def cancelled() -> bool:
        return record.cancel_event.is_set()

    def sink(event: dict) -> None:
        runs.emit(record.run_id, event["kind"], **{
            key: value
            for key, value in event.items()
            if key not in {"id", "run_id", "timestamp", "kind"}
        })

    async def operation():
        return await runtime.chat(task, context, cancel_check=cancelled, event_sink=sink)

    task_handle = asyncio.create_task(runs.start(record.run_id, operation()))
    runs.attach(record.run_id, task_handle)
    return record


@app.get("/ollama")
async def ollama_status():
    session = OllamaTerminalSession()
    return {**detect_ollama(), "reachable": await session.available(), "url": session.base_url, "model": session.model}


@app.post("/learn/remember")
async def learn_remember(request: MemoryRequest):
    return learning.remember(request.text, source="api", kind=request.kind)


@app.get("/learn/recall")
async def learn_recall(query: str, limit: int = 8):
    return {"items": learning.recall(query, limit)}


@app.post("/learn/chat")
async def learn_chat(request: ChatRequest):
    session_id = request.context or "default"
    learning.record_message(session_id, "user", request.task)
    recalled = learning.recall(request.task, limit=8)
    memory_context = "\n".join(item["text"] for item in recalled)
    answer = await OllamaTerminalSession().chat(
        request.task,
        system="You are Nexum Core learning with persistent retrieval memory. "
               "Use recalled facts as context, but do not treat unverified claims as truth. "
               f"Recalled memory:\n{memory_context}",
    )
    learning.record_message(session_id, "assistant", answer)
    return {"session_id": session_id, "answer": answer, "recalled": recalled}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexum-ai-core", "version": "0.6.0"}


@app.get("/agents")
async def agents():
    return {"agents": [a.describe() for a in runtime.orchestrator.agents.values()]}


@app.get("/tools")
async def tools():
    return {"tools": runtime.tools.schemas()}


@app.get("/models")
async def models():
    provider = runtime.router.provider
    return {"provider": type(provider).__name__, "model": getattr(provider, "model", None)}


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
    record = start_run(request.task, request.context)
    try:
        await record.task_handle
    except asyncio.CancelledError:
        pass
    return run_view(runs.get(record.run_id))


@app.post("/runs")
async def create_run(request: ChatRequest):
    return run_view(start_run(request.task, request.context))


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
        runs.get(run_id)
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


@app.post("/projects/state")
async def project_state(request: ProjectRequest):
    return get_project(request.path).state.get()


@app.post("/projects/lifecycle")
async def project_lifecycle(request: ProjectRequest):
    return get_project(request.path).lifecycle(install=True)


@app.post("/projects/checkpoint")
async def project_checkpoint(request: ProjectRequest):
    return get_project(request.path).checkpoint()


@app.post("/projects/restore")
async def project_restore(request: RestoreRequest):
    return get_project(request.path).restore(request.snapshot_id).__dict__


@app.post("/projects/verify-repair")
async def project_verify_repair(request: ProjectRequest):
    return get_project(request.path).verify_and_repair()


@app.post("/projects/preview/start")
async def preview_start(request: ProjectRequest):
    result = get_project(request.path).start_preview()
    return result.__dict__


@app.post("/projects/preview/stop")
async def preview_stop(request: ProjectRequest, pid: int):
    result = get_project(request.path).stop_preview(pid)
    if not result.ok:
        raise HTTPException(status_code=404, detail="Preview process not found")
    return result.__dict__


@app.post("/evals/run")
async def evals_run():
    results = run_runtime_evals()
    return {"ok": all_passed(results), "results": results}

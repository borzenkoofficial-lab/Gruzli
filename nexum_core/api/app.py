from __future__ import annotations
import asyncio, json
from pathlib import Path
from typing import Any, AsyncIterator
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from ..evals.runtime import all_passed, run_runtime_evals
from ..learning.teacher import TeacherLoop
from ..learning.curriculum import AutonomousCurriculum
from ..memory.conversation import LearningMemory
from ..model.terminal import OllamaTerminalSession, detect_ollama
from ..projects.runtime import ProjectRuntime
from ..projects.repair_loop import RepairPlanner
from ..reasoning.state import RunManager
from ..runtime import NexumRuntime
from ..tools.executor import ToolCall
from ..config.settings import settings
from ..research import ResearchEngine

app = FastAPI(title="Nexum AI Core", version="0.8.0")
UI_DIR = Path(__file__).resolve().parent.parent / "ui"
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
runtime = NexumRuntime(".")
runs = RunManager()
learning = LearningMemory(runtime.memory)
teacher = TeacherLoop(learning)
project_runtimes: dict[str, ProjectRuntime] = {}
research = ResearchEngine()

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

class ProjectRunRequest(BaseModel):
    path: str
    operation: str
    install: bool = False

class ProjectCloneRequest(BaseModel):
    repository: str
    path: str
\nclass RepairPlanRequest(BaseModel):
    parsed_error: dict[str, Any] = Field(default_factory=dict)

class RestoreRequest(BaseModel):
    path: str
    snapshot_id: str

class TeacherRequest(BaseModel):
    question: str
    session_id: str = "api"
    remember: bool = True

class TeachRequest(BaseModel):
    questions: list[str]
    session_id: str = "api"

class CurriculumRequest(BaseModel):
    topic: str
    count: int = 5
    session_id: str = "api-curriculum"

@app.get("/", include_in_schema=False)
async def ui_home():
    return FileResponse(UI_DIR / "index.html")

def get_project(path: str) -> ProjectRuntime:
    root = Path(path).resolve()
    allowed = Path(".").resolve()
    try: root.relative_to(allowed)
    except ValueError as exc: raise HTTPException(status_code=403, detail="Project path is outside the AI Core workspace") from exc
    project_runtimes[str(root)] = project_runtimes.get(str(root), ProjectRuntime(str(root)))
    return project_runtimes[str(root)]

def run_view(record) -> dict[str, Any]:
    result = record.result if isinstance(record.result, dict) else None
    return {"run_id": record.run_id, "task": record.task, "status": record.status, "phase": record.phase,
            "iteration": record.iteration, "created_at": record.created_at, "started_at": record.started_at,
            "finished_at": record.finished_at, "result": result, "error": record.error, "event_count": len(record.events)}

def start_run(task: str, context: str = ""):
    record = runs.create(task)
    def cancelled() -> bool: return record.cancel_event.is_set()
    def sink(event: dict) -> None:
        runs.emit(record.run_id, event["kind"], **{k:v for k,v in event.items() if k not in {"id","run_id","timestamp","kind"}})
    async def operation(): return await runtime.chat(task, context, cancel_check=cancelled, event_sink=sink)
    task_handle = asyncio.create_task(runs.start(record.run_id, operation()))
    runs.attach(record.run_id, task_handle)
    return record

@app.get("/ollama")
async def ollama_status():
    session = OllamaTerminalSession()
    return {**detect_ollama(), "reachable": await session.available(), "url": session.base_url, "model": session.model,
            "models": await session.models() if await session.available() else []}

@app.post("/teacher/ask")
async def teacher_ask(request: TeacherRequest):
    result = await teacher.ask(request.question, session_id=request.session_id, remember=request.remember)
    return {"question": result.question, "answer": result.answer, "recalled": result.recalled,
            "memory_item": result.memory_item, "verified": result.verified, "confidence": result.confidence}

@app.post("/teacher/teach")
async def teacher_teach(request: TeachRequest):
    results = await teacher.teach(request.questions, session_id=request.session_id)
    return {"results": [r.__dict__ for r in results]}

@app.post("/teacher/curriculum")
async def teacher_curriculum(request: CurriculumRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="topic is required")
    run = await AutonomousCurriculum(teacher).run(request.topic, request.count, request.session_id)
    return run.__dict__

@app.get("/learn/recall")
async def learn_recall(query: str, limit: int = 8):
    return {"items": learning.recall(query, limit)}

@app.post("/learn/remember")
async def learn_remember(request: MemoryRequest):
    return learning.remember(request.text, source="api", kind=request.kind)

@app.post("/learn/chat")
async def learn_chat(request: ChatRequest):
    session_id = request.context or "default"
    learning.record_message(session_id, "user", request.task)
    recalled = learning.recall(request.task, limit=8)
    memory_context = "\n".join(item["text"] for item in recalled)
    answer = await OllamaTerminalSession().chat(request.task, system="Use memory as context, not unquestioned truth.\n"+memory_context)
    learning.record_message(session_id, "assistant", answer)
    return {"session_id": session_id, "answer": answer, "recalled": recalled}

class ResearchRequest(BaseModel):
    query: str
    urls: list[str] = Field(default_factory=list)

@app.post("/research/fetch")
async def research_fetch(request: ToolRequest):
    if request.name != "web_fetch":
        raise HTTPException(status_code=400, detail="use web_fetch")
    result = runtime.executor.execute(ToolCall("web_fetch", request.arguments))
    return {"ok": result.ok, "output": result.output, "error": result.error}

@app.post("/research/run")
async def research_run(request: ResearchRequest):
    if not request.urls:
        raise HTTPException(status_code=400, detail="urls are required")
    return research.run(request.query, request.urls).__dict__

@app.get("/network")
async def network_status():
    return {"mode": settings.network_mode, "max_bytes": settings.network_max_bytes, "timeout": settings.network_timeout, "tool": "web_fetch"}

@app.get("/health")
async def health(): return {"status":"ok","service":"nexum-ai-core","version":"0.8.0","ui":"/", "network_mode": settings.network_mode}

@app.get("/agents")
async def agents(): return {"agents":[a.describe() for a in runtime.orchestrator.agents.values()]}

@app.get("/tools")
async def tools(): return {"tools":runtime.tools.schemas()}

@app.get("/models")
async def models():
    provider=runtime.router.provider
    return {"provider":type(provider).__name__,"model":getattr(provider,"model",None),"available":runtime.router.available()}

@app.get("/memory")
async def memory(): return {"items":runtime.memory.all()}

@app.post("/memory")
async def add_memory(request: MemoryRequest): return runtime.memory.add(request.text, request.kind)

@app.post("/tools/execute")
async def execute_tool(request: ToolRequest):
    result=runtime.executor.execute(ToolCall(request.name, request.arguments))
    return {"name":result.name,"ok":result.ok,"output":result.output,"error":result.error}

@app.post("/chat")
async def chat(request: ChatRequest):
    record=start_run(request.task,request.context)
    try: await record.task_handle
    except asyncio.CancelledError: pass
    return run_view(runs.get(record.run_id))

@app.post("/runs")
async def create_run(request: ChatRequest): return run_view(start_run(request.task,request.context))

@app.get("/runs")
async def list_runs(): return {"runs":[run_view(record) for record in runs.runs.values()]}

@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    try: return run_view(runs.get(run_id))
    except KeyError as exc: raise HTTPException(status_code=404,detail="Run not found") from exc

@app.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    try: ok=runs.cancel(run_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail="Run not found") from exc
    return {"run_id":run_id,"cancelled":ok,"status":runs.get(run_id).status}

@app.get("/runs/{run_id}/events")
async def run_events(run_id: str):
    try: runs.get(run_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail="Run not found") from exc
    async def stream() -> AsyncIterator[str]:
        sent=0
        while True:
            record=runs.get(run_id)
            while sent<len(record.events):
                event=record.events[sent]; sent+=1
                yield f"data: {json.dumps(event,ensure_ascii=False)}\n\n"
            if record.status in runs.TERMINAL and sent>=len(record.events): break
            await asyncio.sleep(0.15)
    return StreamingResponse(stream(),media_type="text/event-stream")

@app.post("/projects/clone")
async def project_clone(request: ProjectCloneRequest):
    root = Path(request.path).resolve()
    allowed = Path(".").resolve()
    try:
        root.relative_to(allowed)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Project path is outside the AI Core workspace") from exc
    result = runtime.executor.execute(ToolCall("git_workspace", {
        "operation": "clone",
        "path": str(root.relative_to(allowed)),
        "repository": request.repository,
    }))
    return {"ok": result.ok, "output": result.output, "error": result.error}

@app.post("/projects/open")
async def project_open(request: ProjectRequest):
    return get_project(request.path).inspect().__dict__

@app.post("/projects/run")
async def project_run(request: ProjectRunRequest):
    project = get_project(request.path)
    allowed = {"inspect": project.inspect, "install": project.install, "build": project.build, "test": project.test}
    if request.operation not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported project operation")
    result = allowed[request.operation]()
    return result.__dict__

@app.post("/projects/inspect")
async def project_inspect(request: ProjectRequest): return get_project(request.path).inspect().__dict__
@app.post("/projects/state")
async def project_state(request: ProjectRequest): return get_project(request.path).state.get()
@app.post("/projects/lifecycle")
async def project_lifecycle(request: ProjectRequest): return get_project(request.path).lifecycle(install=True)
@app.post("/projects/checkpoint")
async def project_checkpoint(request: ProjectRequest): return get_project(request.path).checkpoint()
@app.post("/projects/restore")
async def project_restore(request: RestoreRequest): return get_project(request.path).restore(request.snapshot_id).__dict__
@app.post("/projects/repair-plan")
async def project_repair_plan(request: RepairPlanRequest):
    plan = RepairPlanner().plan({"parsed_error": request.parsed_error})
    return plan.__dict__

@app.post("/projects/verify-repair")
async def project_verify_repair(request: ProjectRequest): return get_project(request.path).verify_and_repair()
@app.post("/projects/preview/start")
async def preview_start(request: ProjectRequest): return get_project(request.path).start_preview().__dict__
@app.post("/projects/preview/stop")
async def preview_stop(request: ProjectRequest,pid:int):
    result=get_project(request.path).stop_preview(pid)
    if not result.ok: raise HTTPException(status_code=404,detail="Preview process not found")
    return result.__dict__

@app.post("/evals/run")
async def evals_run():
    results=run_runtime_evals()
    return {"ok":all_passed(results),"results":results}

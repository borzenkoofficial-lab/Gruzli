from fastapi import FastAPI
from pydantic import BaseModel, Field
from ..runtime import NexumRuntime
from ..tools.executor import ToolCall

app = FastAPI(title="Nexum AI Core", version="0.2.0")
runtime = NexumRuntime(".")

class ChatRequest(BaseModel):
    task: str
    context: str = ""

class MemoryRequest(BaseModel):
    text: str
    kind: str = "fact"

class ToolRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexum-ai-core", "version": "0.2.0"}

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

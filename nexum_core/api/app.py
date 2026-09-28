from fastapi import FastAPI
from pydantic import BaseModel
from ..runtime import NexumRuntime

app = FastAPI(title="Nexum AI Core", version="0.1.0")
runtime = NexumRuntime(".")

class ChatRequest(BaseModel):
    task: str
    context: str = ""

class MemoryRequest(BaseModel):
    text: str
    kind: str = "fact"

@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexum-ai-core", "version": "0.1.0"}

@app.get("/tools")
async def tools():
    return {"tools": runtime.tools.schemas()}

@app.get("/memory")
async def memory():
    return {"items": runtime.memory.all()}

@app.post("/memory")
async def add_memory(request: MemoryRequest):
    return runtime.memory.add(request.text, request.kind)

@app.post("/chat")
async def chat(request: ChatRequest):
    return await runtime.chat(request.task, request.context)

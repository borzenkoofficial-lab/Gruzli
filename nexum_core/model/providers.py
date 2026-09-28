from __future__ import annotations
import os
from typing import Protocol
import httpx
from .types import GenerationRequest, ModelResponse

class ModelProvider(Protocol):
    name: str
    async def generate(self, request: GenerationRequest) -> ModelResponse: ...

class MockProvider:
    name = "mock"
    async def generate(self, request: GenerationRequest) -> ModelResponse:
        last = next((m for m in reversed(request.messages) if m.role == "user"), None)
        return ModelResponse(
            content=f"[mock] {last.content if last else 'No user message'}",
            model="mock",
        )

class OllamaProvider:
    name = "ollama"
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")

    async def generate(self, request: GenerationRequest) -> ModelResponse:
        prompt = "\n".join(f"{m.role}: {m.content}" for m in request.messages)
        payload = {"model": request.model or self.model, "prompt": prompt, "stream": False,
                   "options": {"temperature": request.temperature, "num_predict": request.max_tokens}}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return ModelResponse(content=data.get("response", ""), model=payload["model"], raw=data)

class OpenAICompatibleProvider:
    name = "openai_compatible"
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def generate(self, request: GenerationRequest) -> ModelResponse:
        payload = {
            "model": request.model or self.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        choice = data["choices"][0]
        return ModelResponse(content=choice["message"]["content"], model=payload["model"], raw=data)

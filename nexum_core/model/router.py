from __future__ import annotations
import os
from typing import Any
from .providers import MockProvider, OllamaProvider, OpenAICompatibleProvider, ModelProvider

class ModelRouter:
    """Capability-aware provider router with deterministic fallback."""
    def __init__(self) -> None:
        self.providers: dict[str, ModelProvider] = {}
        self._register_defaults()
        self.default = os.getenv("AI_PROVIDER", "mock").lower()

    def _register_defaults(self) -> None:
        self.providers["mock"] = MockProvider()
        if os.getenv("OLLAMA_URL") or os.getenv("AI_PROVIDER", "mock").lower() == "ollama":
            self.providers["ollama"] = OllamaProvider()
        if os.getenv("OPENAI_BASE_URL") and os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"):
            self.providers["openai_compatible"] = OpenAICompatibleProvider(
                os.environ["OPENAI_BASE_URL"], os.environ["OPENAI_API_KEY"], os.environ["OPENAI_MODEL"]
            )

    @property
    def provider(self) -> ModelProvider:
        return self.providers.get(self.default, self.providers["mock"])

    def available(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "model": getattr(provider, "model", name)}
            for name, provider in self.providers.items()
        ]

    def select(self, task: str = "", preferred: str | None = None) -> ModelProvider:
        if preferred and preferred in self.providers:
            return self.providers[preferred]
        task_l = task.lower()
        if any(x in task_l for x in ("code", "код", "typescript", "python", "debug", "build")) and "ollama" in self.providers:
            return self.providers["ollama"]
        return self.provider

    async def generate(self, request, preferred: str | None = None):
        task = " ".join(m.content for m in request.messages[-2:])
        provider = self.select(task, preferred)
        try:
            return await provider.generate(request)
        except Exception:
            if provider is not self.providers["mock"]:
                return await self.providers["mock"].generate(request)
            raise

    async def stream(self, request, preferred: str | None = None):
        task = " ".join(m.content for m in request.messages[-2:])
        provider = self.select(task, preferred)
        if hasattr(provider, "stream"):
            async for token in provider.stream(request):
                yield token
            return
        result = await provider.generate(request)
        yield result.content

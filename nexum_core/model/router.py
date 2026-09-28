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

    def register_openai_compatible(self, name: str, base_url: str, api_key: str, model: str) -> None:
        safe_name = name.strip().lower().replace(" ", "_")
        if not safe_name or safe_name in {"mock", "ollama"}:
            raise ValueError("Invalid or reserved provider name")
        self.providers[safe_name] = OpenAICompatibleProvider(base_url, api_key, model)

    def remove(self, name: str) -> bool:
        if name in {"mock", "ollama"}:
            return False
        return self.providers.pop(name, None) is not None

    def _register_defaults(self) -> None:
        self.providers["mock"] = MockProvider()
        if os.getenv("OLLAMA_URL") or os.getenv("AI_PROVIDER", "mock").lower() == "ollama":
            self.providers["ollama"] = OllamaProvider()
        if os.getenv("OPENAI_BASE_URL") and os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"):
            self.providers["openai_compatible"] = OpenAICompatibleProvider(
                os.environ["OPENAI_BASE_URL"], os.environ["OPENAI_API_KEY"], os.environ["OPENAI_MODEL"]
            )
        if os.getenv("DEEPSEEK_API_KEY"):
            self.providers["deepseek"] = OpenAICompatibleProvider(
                os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                os.environ["DEEPSEEK_API_KEY"],
                os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            )
        if os.getenv("OPENAI_API_KEY") and "openai" not in self.providers:
            self.providers["openai"] = OpenAICompatibleProvider(
                os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                os.environ["OPENAI_API_KEY"],
                os.getenv("OPENAI_MODEL", "gpt-4.1"),
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

    async def generate_with_provider(self, request, provider_name: str):
        provider = self.providers.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name}")
        return await provider.generate(request)

    async def stream_with_provider(self, request, provider_name: str):
        provider = self.providers.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name}")
        if hasattr(provider, "stream"):
            async for token in provider.stream(request):
                yield token
            return
        result = await provider.generate(request)
        yield result.content

    async def stream(self, request, preferred: str | None = None):
        task = " ".join(m.content for m in request.messages[-2:])
        provider = self.select(task, preferred)
        if hasattr(provider, "stream"):
            async for token in provider.stream(request):
                yield token
            return
        result = await provider.generate(request)
        yield result.content

from __future__ import annotations
import os
from typing import Any
from .providers import MockProvider, OllamaProvider, OpenAICompatibleProvider, ModelProvider
from ..config.settings import settings

class ModelRouter:
    """Capability-aware provider router with deterministic fallback."""
    def __init__(self) -> None:
        self.providers: dict[str, ModelProvider] = {}
        self._register_defaults()
        self.default = settings.ai_provider.lower()

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
        if settings.ollama_url or settings.ai_provider.lower() == "ollama":
            self.providers["ollama"] = OllamaProvider(settings.ollama_url, settings.ollama_model)
        if os.getenv("OPENAI_BASE_URL") and settings.openai_api_key and os.getenv("OPENAI_MODEL"):
            self.providers["openai_compatible"] = OpenAICompatibleProvider(
                os.environ["OPENAI_BASE_URL"], settings.openai_api_key, os.environ["OPENAI_MODEL"]
            )
        if settings.deepseek_api_key:
            self.providers["deepseek"] = OpenAICompatibleProvider(
                settings.deepseek_base_url,
                settings.deepseek_api_key,
                settings.deepseek_model,
            )
        if os.getenv("OPENAI_API_KEY") and "openai" not in self.providers:
            self.providers["openai"] = OpenAICompatibleProvider(
                settings.openai_base_url,
                os.environ["OPENAI_API_KEY"],
                settings.openai_model,
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

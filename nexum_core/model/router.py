from __future__ import annotations
import os
from .providers import MockProvider, OllamaProvider, OpenAICompatibleProvider, ModelProvider

class ModelRouter:
    def __init__(self) -> None:
        provider = os.getenv("AI_PROVIDER", "mock").lower()
        if provider == "ollama":
            self.provider: ModelProvider = OllamaProvider()
        elif provider in {"openai", "openai_compatible"}:
            self.provider = OpenAICompatibleProvider(
                os.environ["OPENAI_BASE_URL"], os.environ["OPENAI_API_KEY"], os.environ["OPENAI_MODEL"]
            )
        else:
            self.provider = MockProvider()

    async def generate(self, request):
        return await self.provider.generate(request)

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]

@dataclass
class Message:
    role: Role
    content: str
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelResponse:
    content: str
    model: str
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None

@dataclass
class GenerationRequest:
    messages: list[Message]
    model: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2048
    tools: list[dict[str, Any]] = field(default_factory=list)

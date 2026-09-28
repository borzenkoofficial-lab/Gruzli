from dataclasses import dataclass, field
from typing import Any

@dataclass
class Message:
    role: str
    content: str
    tool_calls: list["ToolCall"] = field(default_factory=list)

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationRequest:
    messages: list[Message]
    max_tokens: int = 2048
    model: str | None = None
    temperature: float = 0.2

@dataclass
class GenerationResult:
    content: str
    model: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None

# Backward-compatible public name used by providers and older runtime code.
ModelResponse = GenerationResult

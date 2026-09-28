from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .registry import ToolRegistry

@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolResult:
    name: str
    ok: bool
    output: Any = None
    error: str | None = None

class ToolExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, call: ToolCall) -> ToolResult:
        try:
            tool = self.registry.get(call.name)
            return ToolResult(call.name, True, tool.execute(**call.arguments))
        except Exception as exc:
            return ToolResult(call.name, False, error=f"{type(exc).__name__}: {exc}")

import json
from typing import Any
from .base import Tool

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        if not tool.name:
            raise ValueError('Tool name is required')
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f'Unknown tool: {name}')
        return self._tools[name]

    def validate_arguments(self, name: str, arguments: dict[str, Any]) -> None:
        tool = self.get(name)
        schema = tool.parameters
        required = set(schema.get('required', []))
        missing = required - set(arguments)
        if missing:
            raise ValueError(f'Missing required arguments for {name}: {sorted(missing)}')
        allowed = set(schema.get('properties', {}))
        unknown = set(arguments) - allowed
        if unknown and schema.get('additionalProperties') is False:
            raise ValueError(f'Unknown arguments for {name}: {sorted(unknown)}')

    def schemas(self):
        return [tool.schema() for tool in self._tools.values()]

    def prompt_schemas(self) -> str:
        return json.dumps(self.schemas(), ensure_ascii=False, separators=(',', ':'))

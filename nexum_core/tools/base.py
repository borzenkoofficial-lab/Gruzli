from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]
    schema: dict[str, Any] = field(default_factory=dict)

    def execute(self, **kwargs):
        return self.handler(**kwargs)

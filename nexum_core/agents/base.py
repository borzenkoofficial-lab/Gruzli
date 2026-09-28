from dataclasses import dataclass, field
from typing import Any

@dataclass
class Agent:
    name: str
    system_prompt: str
    capabilities: list[str] = field(default_factory=list)

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "capabilities": self.capabilities, "system_prompt": self.system_prompt}

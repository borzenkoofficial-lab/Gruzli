from abc import ABC, abstractmethod
from typing import Any

class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any] = {'type': 'object', 'properties': {}, 'additionalProperties': False}

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        raise NotImplementedError

    def schema(self) -> dict[str, Any]:
        return {'name': self.name, 'description': self.description, 'parameters': self.parameters}

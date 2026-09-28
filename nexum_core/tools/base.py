from abc import ABC, abstractmethod
from typing import Any

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        raise NotImplementedError

    def schema(self) -> dict:
        return {"name": self.name, "description": self.description}

"""Project subsystem public API.

Imports are intentionally lazy to avoid circular imports between project
runtime and tool implementations.
"""

from .manager import ProjectManager
from .templates import create_react_vite_template
from .state import ProjectState
from .dev_server import DevServerManager
from .error_parser import ErrorParser
from .sandbox import Sandbox, SandboxPolicy
from .repair import RepairEngine

__all__ = [
    "ProjectManager",
    "ProjectRuntime",
    "ProjectState",
    "DevServerManager",
    "ErrorParser",
    "Sandbox",
    "SandboxPolicy",
    "RepairEngine",
    "create_react_vite_template",
]


def __getattr__(name: str):
    if name == "ProjectRuntime":
        from .runtime import ProjectRuntime
        return ProjectRuntime
    raise AttributeError(name)

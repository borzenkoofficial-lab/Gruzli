from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SandboxPolicy:
    allow_network: bool = False
    max_timeout: int = 120
    max_output: int = 20000
    allow_commands: tuple[str, ...] = ("python", "python3", "node", "npm", "npx", "pnpm", "pytest")


class Sandbox:
    def __init__(self, root: str, policy: SandboxPolicy | None = None):
        self.root = Path(root).resolve()
        self.policy = policy or SandboxPolicy()

    def validate_path(self, path: str) -> Path:
        target = (self.root / path).resolve()
        target.relative_to(self.root)
        return target

    def validate_command(self, command: str, timeout: int) -> None:
        if command not in self.policy.allow_commands:
            raise PermissionError(f"Command denied: {command}")
        if timeout < 1 or timeout > self.policy.max_timeout:
            raise ValueError("Timeout exceeds sandbox policy")

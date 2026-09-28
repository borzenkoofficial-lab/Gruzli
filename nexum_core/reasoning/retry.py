from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetryBudget:
    max_retries: int = 3
    used: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)

    @property
    def remaining(self) -> int:
        return max(0, self.max_retries - self.used)

    def consume(self, category: str, message: str) -> bool:
        if self.remaining <= 0:
            return False
        self.used += 1
        self.failures.append({"attempt": self.used, "category": category, "message": message})
        return True

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class DatasetRecord:
    kind: str
    input: str
    output: str
    metadata: dict[str, Any]
    score: float = 0.0

    def valid(self) -> bool:
        return bool(self.input.strip() and self.output.strip() and self.score >= 0.7)

class DatasetStore:
    def __init__(self, path: str = "data/datasets/validated.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: DatasetRecord) -> bool:
        if not record.valid():
            return False
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.__dict__, ensure_ascii=False) + "\n")
        return True

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x.strip()]

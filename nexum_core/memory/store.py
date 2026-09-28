from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class MemoryStore:
    def __init__(self, path: str = "data/memory.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, text: str, kind: str = "fact", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        item = {"text": text, "kind": kind, "metadata": metadata or {}}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return item

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        terms = set(query.lower().split())
        scored = []
        for item in self.all():
            text = item.get("text", "").lower()
            score = sum(1 for term in terms if term in text)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any


class RunPersistence:
    """Append-only persistence for resumable execution metadata."""

    def __init__(self, path: str = "data/runs.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: Any) -> None:
        payload = asdict(record) if hasattr(record, "__dataclass_fields__") else dict(record)
        payload.pop("task_handle", None)
        payload.pop("cancel_event", None)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

    def latest(self, run_id: str) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        found = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            item = json.loads(line)
            if item.get("run_id") == run_id:
                found = item
        return found

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]

from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .trajectory import Trajectory

class TrajectoryStore:
    def __init__(self, path: str = "data/trajectories.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, trajectory: Trajectory) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trajectory.to_training_record(), ensure_ascii=False) + "\n")

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x.strip()]

    def verified(self) -> list[dict[str, Any]]:
        return [x for x in self.all() if x.get("success") and x.get("verification", {}).get("ok")]

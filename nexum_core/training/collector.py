import json
from pathlib import Path
from .trajectory import Trajectory

class TrajectoryCollector:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, trajectory: Trajectory):
        record = trajectory.to_training_record()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def all(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def verified(self) -> list[dict]:
        return [item for item in self.all() if item.get("success") and item.get("verification", {}).get("ok")]

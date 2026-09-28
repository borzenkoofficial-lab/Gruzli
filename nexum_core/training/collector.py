import json
from pathlib import Path
from .trajectory import Trajectory

class TrajectoryCollector:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, trajectory: Trajectory):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trajectory.__dict__, ensure_ascii=False) + "\n")

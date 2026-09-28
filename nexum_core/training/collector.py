import json
from pathlib import Path
from .schema import Trajectory

class TrajectoryCollector:
    def __init__(self, path="datasets/raw/trajectories.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, trajectory: Trajectory):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trajectory.to_dict(), ensure_ascii=False) + "\n")

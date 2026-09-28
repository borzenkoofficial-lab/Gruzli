from __future__ import annotations
import json
from pathlib import Path
from nexum_core.training.collector import TrajectoryCollector
from nexum_core.training.dataset import DatasetRecord, DatasetStore
from nexum_core.training.quality import DatasetQuality

def main():
    collector = TrajectoryCollector("data/memory/trajectories.jsonl")
    dataset = DatasetStore("data/datasets/validated.jsonl")
    count = 0
    for item in collector.verified():
        messages = item.get("messages", [])
        user = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
        answer = next((m.get("content", "") for m in messages if m.get("role") == "model"), "")
        if user and answer:
            count += dataset.append(DatasetRecord("trajectory", user, answer, {"run_id": item.get("run_id")}, 0.85))
    print(f"exported={count}")

if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import shutil
import time


@dataclass
class Snapshot:
    id: str
    path: str
    created_at: float
    files: int


class ProjectState:
    STATES = {"created", "installing", "ready", "building", "testing", "running", "failed", "stopped"}

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.state_file = self.root / ".nexum" / "state.json"
        self.snapshot_root = self.root / ".nexum" / "snapshots"
        self.snapshot_root.mkdir(parents=True, exist_ok=True)

    def set(self, state: str, **metadata: Any) -> dict[str, Any]:
        if state not in self.STATES:
            raise ValueError(f"Unknown project state: {state}")
        data = {"state": state, "updated_at": time.time(), **metadata}
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def get(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return self.set("created")
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def snapshot(self, label: str = "checkpoint") -> Snapshot:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)[:60]
        sid = f"{int(time.time() * 1000)}-{safe}"
        target = self.snapshot_root / sid
        target.mkdir(parents=True, exist_ok=False)
        excluded = {".git", ".nexum", "node_modules", "__pycache__", ".venv"}
        count = 0
        for source in self.root.rglob("*"):
            if not source.is_file() or any(part in excluded for part in source.relative_to(self.root).parts):
                continue
            relative = source.relative_to(self.root)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            count += 1
        return Snapshot(sid, str(target), time.time(), count)

    def restore(self, snapshot_id: str) -> bool:
        source = self.snapshot_root / snapshot_id
        if not source.is_dir():
            return False
        excluded = {".git", ".nexum", "node_modules", "__pycache__", ".venv"}
        for path in sorted(self.root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if not path.is_file() or any(part in excluded for part in path.relative_to(self.root).parts):
                continue
            path.unlink()
        for source_file in source.rglob("*"):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source)
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination)
        return True

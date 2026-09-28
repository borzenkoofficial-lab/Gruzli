from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExecutionState:
    task: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    phase: str = "planning"
    iteration: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    verified: bool = False
    errors: list[str] = field(default_factory=list)

    def event(self, kind: str, **data):
        self.events.append({
            "id": str(uuid4()),
            "run_id": self.run_id,
            "timestamp": now(),
            "kind": kind,
            **data,
        })


@dataclass
class RunRecord:
    task: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "queued"
    created_at: str = field(default_factory=now)
    started_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    task_handle: asyncio.Task | None = field(default=None, repr=False, compare=False)


class RunManager:
    TERMINAL = {"succeeded", "failed", "cancelled"}

    def __init__(self):
        self.runs: dict[str, RunRecord] = {}

    def create(self, task: str) -> RunRecord:
        record = RunRecord(task=task)
        self.runs[record.run_id] = record
        self.emit(record.run_id, "run_queued", task=task)
        return record

    def emit(self, run_id: str, kind: str, **data: Any) -> None:
        record = self.runs[run_id]
        record.events.append({
            "id": str(uuid4()),
            "run_id": run_id,
            "timestamp": now(),
            "kind": kind,
            **data,
        })

    async def start(self, run_id: str, operation) -> RunRecord:
        record = self.runs[run_id]
        record.status = "running"
        record.started_at = now()
        self.emit(run_id, "run_started")
        try:
            record.result = await operation()
            record.status = "succeeded" if record.result.get("verified", False) else "failed"
            self.emit(run_id, "run_finished", status=record.status, verified=record.result.get("verified", False))
        except asyncio.CancelledError:
            record.status = "cancelled"
            record.finished_at = now()
            self.emit(run_id, "run_cancelled")
            raise
        except Exception as exc:
            record.status = "failed"
            record.error = f"{type(exc).__name__}: {exc}"
            self.emit(run_id, "run_failed", error=record.error)
        finally:
            record.finished_at = record.finished_at or now()
        return record

    def attach(self, run_id: str, task: asyncio.Task) -> None:
        self.runs[run_id].task_handle = task

    def get(self, run_id: str) -> RunRecord:
        if run_id not in self.runs:
            raise KeyError(run_id)
        return self.runs[run_id]

    def cancel(self, run_id: str) -> bool:
        record = self.get(run_id)
        if record.status in self.TERMINAL:
            return False
        if record.task_handle and not record.task_handle.done():
            record.task_handle.cancel()
            return True
        record.status = "cancelled"
        record.finished_at = now()
        self.emit(run_id, "run_cancelled")
        return True

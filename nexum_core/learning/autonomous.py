from __future__ import annotations
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..training.collector import TrajectoryCollector
from ..training.quality import DatasetQuality
from ..training.preferences import from_verification


@dataclass
class LearningCycle:
    total_trajectories: int
    verified: int
    accepted: int
    sft_records: int
    dpo_records: int
    status: str
    generated_at: str
    dataset: str


class AutonomousLearningEngine:
    """Turns verified agent experience into gated training data and optional local training."""

    def __init__(self, root: str = "."):
        self.root = Path(root).resolve()
        self.trajectories = TrajectoryCollector(str(self.root / "data/memory/trajectories.jsonl"))
        self.quality = DatasetQuality(min_score=0.7)
        self.sft_path = self.root / "datasets/processed/sft.jsonl"
        self.dpo_path = self.root / "datasets/preferences/dpo.jsonl"
        self.state_path = self.root / "data/learning/state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.sft_path.parent.mkdir(parents=True, exist_ok=True)
        self.dpo_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"trained_runs": [], "promoted_checkpoint": None, "last_cycle": None}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _save_state(self, state: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _sft_record(record: dict[str, Any]) -> dict[str, Any]:
        messages = list(record.get("messages") or [])
        if not messages:
            messages = [{"role": "user", "content": record.get("task", "")}]
        return {"messages": messages, "metadata": {"run_id": record.get("run_id"), "verification": record.get("verification", {})}}

    def cycle(self) -> LearningCycle:
        all_records = self.trajectories.all()
        verified = [r for r in all_records if r.get("success") and (r.get("verification") or {}).get("ok")]
        accepted = self.quality.filter(verified)

        existing = set()
        if self.sft_path.exists():
            for line in self.sft_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        existing.add((json.loads(line).get("metadata") or {}).get("run_id"))
                    except json.JSONDecodeError:
                        pass

        sft_added = 0
        with self.sft_path.open("a", encoding="utf-8") as f:
            for record in accepted:
                run_id = record.get("run_id")
                if run_id in existing:
                    continue
                f.write(json.dumps(self._sft_record(record), ensure_ascii=False) + "\n")
                existing.add(run_id)
                sft_added += 1

        dpo_added = 0
        candidates = [
            {"verified": bool(r.get("success") and (r.get("verification") or {}).get("ok")), "answer": next(
                (m.get("content", "") for m in reversed(r.get("messages") or []) if m.get("role") in {"model", "assistant"}), ""
            )}
            for r in all_records
        ]
        preference = from_verification("Verified trajectory preference", candidates)
        if preference:
            with self.dpo_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(preference, ensure_ascii=False) + "\n")
            dpo_added = 1

        state = self._load_state()
        state["last_cycle"] = datetime.now(timezone.utc).isoformat()
        self._save_state(state)
        return LearningCycle(
            total_trajectories=len(all_records),
            verified=len(verified),
            accepted=len(accepted),
            sft_records=sft_added,
            dpo_records=dpo_added,
            status="ready_for_training" if accepted else "waiting_for_verified_experience",
            generated_at=state["last_cycle"],
            dataset=str(self.sft_path),
        )

    def status(self) -> dict[str, Any]:
        state = self._load_state()
        sft = sum(1 for _ in self.sft_path.open(encoding="utf-8")) if self.sft_path.exists() else 0
        dpo = sum(1 for _ in self.dpo_path.open(encoding="utf-8")) if self.dpo_path.exists() else 0
        return {
            "trajectories": len(self.trajectories.all()),
            "verified_trajectories": len(self.trajectories.verified()),
            "sft_records": sft,
            "dpo_records": dpo,
            "promoted_checkpoint": state.get("promoted_checkpoint"),
            "last_cycle": state.get("last_cycle"),
        }

    def train_sft(self, model: str, output: str = "artifacts/sft", min_records: int = 8) -> dict[str, Any]:
        cycle = self.cycle()
        count = cycle.accepted
        if count < min_records:
            return {"ok": False, "status": "insufficient_data", "required": min_records, "available": count}

        command = [
            sys.executable, "scripts/train_sft_current.py",
            "--model", model,
            "--dataset", str(self.sft_path),
            "--out", output,
        ]
        process = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=3600)
        ok = process.returncode == 0 and Path(output).exists()
        state = self._load_state()
        if ok:
            state["candidate_checkpoint"] = str(Path(output).resolve())
            state["candidate_records"] = count
        self._save_state(state)
        return {
            "ok": ok,
            "status": "candidate_ready" if ok else "training_failed",
            "checkpoint": str(Path(output).resolve()),
            "records": count,
            "stdout": process.stdout[-4000:],
            "stderr": process.stderr[-4000:],
        }

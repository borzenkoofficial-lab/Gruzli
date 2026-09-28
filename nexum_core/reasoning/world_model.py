from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import json
from pathlib import Path

@dataclass
class Belief:
    statement: str
    confidence: float = 0.5
    evidence: list[str] = field(default_factory=list)
    status: str = "hypothesis"
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WorldModel:
    def __init__(self, path: str = "data/memory/world_model.json"):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.beliefs: list[Belief]=[]
        self.load()

    def load(self):
        if self.path.exists():
            self.beliefs=[Belief(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]

    def save(self):
        self.path.write_text(json.dumps([b.__dict__ for b in self.beliefs],ensure_ascii=False,indent=2),encoding="utf-8")

    def observe(self, statement: str, evidence: str = "", confidence: float = 0.5):
        for b in self.beliefs:
            if b.statement.strip().lower()==statement.strip().lower():
                b.confidence=max(b.confidence, confidence)
                if evidence and evidence not in b.evidence: b.evidence.append(evidence)
                b.updated_at=datetime.now(timezone.utc).isoformat()
                self.save(); return b
        b=Belief(statement, max(0.0,min(1.0,confidence)), [evidence] if evidence else [])
        self.beliefs.append(b); self.save(); return b

    def search(self, query: str, limit: int=8):
        terms=set(query.lower().split())
        ranked=[]
        for b in self.beliefs:
            score=sum(t in b.statement.lower() for t in terms)+0.5*sum(t in " ".join(b.evidence).lower() for t in terms)
            if score: ranked.append((score,b))
        ranked.sort(key=lambda x:x[0], reverse=True)
        return [b.__dict__ for _,b in ranked[:limit]]

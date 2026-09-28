from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from .store import MemoryStore

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class LearningSession:
    session_id: str
    topic: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    learned: list[dict[str, Any]] = field(default_factory=list)

class LearningMemory:
    """Persistent retrieval memory with provenance; this is not weight training."""
    def __init__(self, store: MemoryStore):
        self.store = store
        self.sessions: dict[str, LearningSession] = {}

    def start(self, session_id: str, topic: str = "general") -> LearningSession:
        session = LearningSession(session_id, topic)
        self.sessions[session_id] = session
        return session

    def remember(self, text: str, *, source: str, kind: str = "learned_fact",
                 session_id: str | None = None, confidence: float = 1.0) -> dict[str, Any]:
        item = self.store.add(text, kind, {"source": source, "session_id": session_id,
            "confidence": max(0.0, min(1.0, confidence)), "learned_at": now()})
        if session_id and session_id in self.sessions:
            self.sessions[session_id].learned.append(item)
        return item

    def recall(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        return self.store.search(query, limit)

    def record_message(self, session_id: str, role: str, content: str) -> None:
        session = self.sessions.setdefault(session_id, LearningSession(session_id, "general"))
        session.messages.append({"timestamp": now(), "role": role, "content": content})

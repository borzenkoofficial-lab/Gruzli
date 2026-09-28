from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ..memory.store import MemoryStore
from ..reasoning.world_model import WorldModel

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: str = field(default_factory=now)

@dataclass
class ConversationState:
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    turns: list[ConversationTurn] = field(default_factory=list)
    topic: str = ""
    intent: str = "unknown"

class ConversationEngine:
    """Conversation state, intent hints and durable memory extraction.

    This layer does not replace the language model; it supplies the model with
    structured conversational context and persists useful verified facts.
    """
    def __init__(self, memory: MemoryStore | None = None, world: WorldModel | None = None):
        self.memory = memory or MemoryStore("data/memory/conversations.jsonl")
        self.world = world or WorldModel()

    def observe_user(self, state: ConversationState, text: str) -> dict[str, Any]:
        state.turns.append(ConversationTurn("user", text))
        state.intent = self.classify_intent(text)
        return {"intent": state.intent, "context": self.context(state)}

    def observe_assistant(self, state: ConversationState, text: str, verified: bool = False):
        state.turns.append(ConversationTurn("assistant", text))
        if verified and text.strip():
            self.memory.add(text, kind="verified_dialogue", metadata={"conversation_id": state.conversation_id})
        return self.context(state)

    def classify_intent(self, text: str) -> str:
        t=text.strip().lower()
        if not t: return "empty"
        if t.endswith("?") or any(t.startswith(x) for x in ("как ", "почему ", "зачем ", "что ", "где ", "когда ", "можно ли ")):
            return "question"
        if any(x in t for x in ("сделай", "создай", "добавь", "исправь", "запусти", "проверь", "сделай всё")):
            return "command"
        if any(x in t for x in ("нет,", "не так", "исправь", "я имел в виду", "неправильно")):
            return "correction"
        return "conversation"

    def context(self, state: ConversationState, limit: int = 12) -> dict[str, Any]:
        turns=state.turns[-limit:]
        return {
            "conversation_id": state.conversation_id,
            "intent": state.intent,
            "topic": state.topic,
            "turns":[{"role":t.role,"content":t.content,"timestamp":t.timestamp} for t in turns],
            "memory": self.memory.search(" ".join(t.content for t in turns[-4:]), limit=6),
            "world": self.world.search(" ".join(t.content for t in turns[-4:]), limit=6),
        }

from __future__ import annotations
from .specialists import SPECIALISTS

class Orchestrator:
    def __init__(self):
        self.agents = {agent.name: agent for agent in SPECIALISTS}

    def select(self, task: str) -> list[str]:
        t = task.lower()
        selected = []
        rules = {
            "programmer": ("code", "python", "typescript", "bug", "implement", "refactor"),
            "designer": ("design", "ui", "ux", "interface", "layout"),
            "vision": ("image", "screenshot", "visual", "picture"),
            "researcher": ("research", "source", "compare", "latest", "verify"),
            "tester": ("test", "debug", "failure", "verify"),
            "architect": ("architecture", "system", "plan", "project"),
        }
        for name, words in rules.items():
            if any(w in t for w in words):
                selected.append(name)
        return selected or ["architect", "programmer", "tester"]

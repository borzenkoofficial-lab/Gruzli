from __future__ import annotations
from typing import Any

def make_preference(prompt: str, chosen: str, rejected: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if not prompt.strip() or not chosen.strip() or not rejected.strip():
        raise ValueError("prompt, chosen and rejected are required")
    return {
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
        "metadata": metadata or {},
    }

def from_verification(prompt: str, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid = [x for x in candidates if x.get("verified") and x.get("answer")]
    invalid = [x for x in candidates if not x.get("verified") and x.get("answer")]
    if not valid or not invalid:
        return None
    return make_preference(prompt, valid[0]["answer"], invalid[0]["answer"])

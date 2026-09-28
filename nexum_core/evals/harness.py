from .cases import CASES

def run_static_evals() -> list[dict]:
    return [{"id": c["id"], "status": "pending", "task": c["task"]} for c in CASES]

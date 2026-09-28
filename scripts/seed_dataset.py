import json
from pathlib import Path

rows = [
    {"task":"Create a health endpoint","messages":[{"role":"user","content":"Create a health endpoint"},{"role":"assistant","content":"Implemented /health and verified HTTP 200."}],"actions":[],"outcome":"verified","success":True},
    {"task":"Fix traversal","messages":[{"role":"user","content":"Prevent workspace traversal"},{"role":"assistant","content":"Resolved paths and enforced root containment."}],"actions":[],"outcome":"verified","success":True},
]
p = Path("datasets/raw/trajectories.jsonl")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
print(f"seeded {len(rows)} trajectories")

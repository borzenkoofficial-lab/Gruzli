import json
from pathlib import Path

def prepare(input_path, output_path):
    rows = []
    for line in Path(input_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("success"):
            rows.append({"messages": item.get("messages", [])})
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    return len(rows)

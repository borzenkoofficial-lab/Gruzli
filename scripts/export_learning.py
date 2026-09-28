from __future__ import annotations
import json
from pathlib import Path
from nexum_core.memory.store import MemoryStore

def main():
    source = Path("data/memory.jsonl")
    target = Path("data/datasets/teacher_lessons.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    items = MemoryStore(str(source)).all()
    exported = 0
    with target.open("w", encoding="utf-8") as f:
        for item in items:
            if item.get("kind") != "teacher_lesson":
                continue
            text = item.get("text", "")
            if "Question: " not in text or "\nAnswer: " not in text:
                continue
            question, answer = text.split("\nAnswer: ", 1)
            record = {
                "messages": [
                    {"role": "user", "content": question.removeprefix("Question: ")},
                    {"role": "assistant", "content": answer},
                ],
                "metadata": item.get("metadata", {}),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            exported += 1
    print(f"exported={exported} -> {target}")

if __name__ == "__main__":
    main()

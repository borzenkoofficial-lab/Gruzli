from __future__ import annotations
import argparse, asyncio
from nexum_core.memory.conversation import LearningMemory
from nexum_core.memory.store import MemoryStore
from nexum_core.model.terminal import OllamaTerminalSession
from nexum_core.learning.teacher import TeacherLoop

async def main():
    parser = argparse.ArgumentParser(description="Interactive Nexum Core <-> Ollama teacher terminal")
    parser.add_argument("--model", default=None)
    parser.add_argument("--session", default="terminal")
    args = parser.parse_args()
    teacher = OllamaTerminalSession(model=args.model)
    if not await teacher.available():
        raise SystemExit("Ollama is not reachable. Start Ollama and install the selected model.")
    loop = TeacherLoop(LearningMemory(MemoryStore()), teacher)
    print(f"Nexum Core teacher terminal | model={teacher.model}")
    print("Commands: /memory <query>, /quit")
    while True:
        try: question = input("nexum> ").strip()
        except (EOFError, KeyboardInterrupt): print(); break
        if not question: continue
        if question in {"/quit", "/exit"}: break
        if question.startswith("/memory "):
            for item in loop.memory.recall(question[8:], 10): print(f"[memory] {item.get('text', '')}")
            continue
        result = await loop.ask(question, session_id=args.session)
        print(f"qwen> {result.answer}")
        if result.memory_item: print("[learned] saved to persistent memory")

if __name__ == "__main__":
    asyncio.run(main())

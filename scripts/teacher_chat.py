from __future__ import annotations
import argparse, asyncio
from nexum_core.memory.conversation import LearningMemory
from nexum_core.memory.store import MemoryStore
from nexum_core.model.terminal import OllamaTerminalSession
from nexum_core.learning.teacher import TeacherLoop

async def main():
    parser = argparse.ArgumentParser(description="Nexum Core <-> Ollama interactive terminal")
    parser.add_argument("--model", default=None)
    parser.add_argument("--session", default="terminal")
    args = parser.parse_args()
    teacher = OllamaTerminalSession(model=args.model)
    if not await teacher.available():
        raise SystemExit("Ollama is not reachable. Start Ollama and install the selected model.")
    print(f"Nexum Core terminal | model={teacher.model}")
    print("Commands: /models, /memory <query>, /remember <text>, /quit")
    loop = TeacherLoop(LearningMemory(MemoryStore()), teacher)
    while True:
        try: question = input("nexum> ").strip()
        except (EOFError, KeyboardInterrupt): print(); break
        if not question: continue
        if question in {"/quit", "/exit"}: break
        if question == "/models":
            for name in await teacher.models(): print(f"  - {name}")
            continue
        if question.startswith("/memory "):
            for item in loop.memory.recall(question[8:], 10): print(f"[memory] {item.get('text', '')}")
            continue
        if question.startswith("/remember "):
            loop.memory.remember(question[10:], source="user:terminal", kind="user_fact")
            print("[memory] saved")
            continue
        print("qwen> ", end="", flush=True)
        answer_parts = []
        async for token in teacher.stream(question, system="Answer clearly and precisely."):
            print(token, end="", flush=True)
            answer_parts.append(token)
        answer = "".join(answer_parts)
        print()
        loop.memory.record_message(args.session, "user", question)
        loop.memory.record_message(args.session, "assistant", answer)
        if answer.strip():
            loop.memory.remember(
                f"Question: {question}\nAnswer: {answer}",
                source=f"ollama:{teacher.model}", kind="conversation", session_id=args.session, confidence=0.5
            )
            print("[memory] conversation saved")

if __name__ == "__main__":
    asyncio.run(main())

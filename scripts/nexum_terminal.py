from __future__ import annotations
import argparse
import asyncio
from nexum_core.model.terminal import OllamaTerminalSession

async def main() -> None:
    parser = argparse.ArgumentParser(description="Nexum Core live model terminal")
    parser.add_argument("--model", default=None)
    parser.add_argument("--system", default="You are Nexum AI Core. Be precise, concise, and technical.")
    args = parser.parse_args()

    session = OllamaTerminalSession(model=args.model)
    if not await session.available():
        raise SystemExit(
            f"Ollama is unavailable at {session.base_url}. "
            "Start Ollama and make sure the selected model is installed."
        )

    print(f"Nexum Core live terminal | model={session.model}")
    print("Type /quit to exit, /models to list local models.")
    print()

    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not prompt:
            continue
        if prompt in {"/quit", "/exit"}:
            break
        if prompt == "/models":
            for name in await session.models():
                print(f"  {name}")
            continue

        print("nexum> ", end="", flush=True)
        try:
            async for token in session.stream(prompt, system=args.system):
                print(token, end="", flush=True)
            print()
        except Exception as exc:
            print(f"\n[terminal error] {exc}")

if __name__ == "__main__":
    asyncio.run(main())

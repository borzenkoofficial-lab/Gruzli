from __future__ import annotations
import argparse
import asyncio
from nexum_core.runtime import NexumRuntime

async def main() -> None:
    parser = argparse.ArgumentParser(description="Nexum Core autonomous Agent Loop terminal")
    parser.add_argument("task", nargs="*", help="task for Nexum")
    args = parser.parse_args()

    task = " ".join(args.task).strip()
    if not task:
        task = input("you> ").strip()
    if not task:
        return

    runtime = NexumRuntime(".")
    print("\nNEXUM CORE — autonomous terminal")
    print("=" * 60)
    print(f"TASK: {task}\n")

    def event(event: dict) -> None:
        kind = event.get("kind", "event")
        if kind == "model_output":
            content = event.get("content", "")
            print(f"\n[nexum:model] {content}")
        elif kind == "action_requested":
            print(f"\n[nexum:tool] {event.get('tool')} {event.get('arguments')}")
        elif kind == "tool_result":
            status = "OK" if event.get("ok") else "FAIL"
            print(f"[nexum:result:{status}] {event.get('tool')}: {event.get('output') or event.get('error')}")
        elif kind == "repair_plan":
            print(f"\n[nexum:repair] {event.get('instruction')}")
        elif kind == "verification":
            print(f"\n[nexum:verify] ok={event.get('ok')} evidence={event.get('evidence')}")
        elif kind in {"plan", "repair", "run_cancelled"}:
            print(f"\n[nexum:{kind}] {event}")

    result = await runtime.chat(task, event_sink=event)
    print("\n" + "=" * 60)
    print(f"FINAL | verified={result.get('verified')} | iterations={result.get('iterations')}")
    print(result.get("answer", ""))

if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations
import asyncio, os, shutil
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

@dataclass
class TerminalLine:
    stream: str
    text: str

class OllamaTerminalSession:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")

    async def chat(self, prompt: str, system: str = "") -> str:
        import httpx
        payload = {"model": self.model, "prompt": f"{system}\n\nuser: {prompt}".strip(), "stream": False}
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")

    async def available(self) -> bool:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                return (await client.get(f"{self.base_url}/api/tags")).is_success
        except Exception:
            return False

class InteractiveModelTerminal:
    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace).resolve()

    async def run_command(self, command: str, args: list[str] | None = None) -> AsyncIterator[TerminalLine]:
        process = await asyncio.create_subprocess_exec(command, *(args or []), cwd=self.workspace,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        assert process.stdout is not None
        async for raw in process.stdout:
            yield TerminalLine("stdout", raw.decode(errors="replace").rstrip())
        await process.wait()

def detect_ollama() -> dict:
    executable = shutil.which("ollama")
    return {"installed": bool(executable), "executable": executable}

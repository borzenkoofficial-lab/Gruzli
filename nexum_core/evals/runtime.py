from dataclasses import dataclass
from pathlib import Path
import tempfile

from ..runtime import NexumRuntime


@dataclass
class EvalResult:
    id: str
    ok: bool
    details: dict

    def as_dict(self) -> dict:
        return {"id": self.id, "ok": self.ok, "details": self.details}


def run_runtime_evals() -> list[dict]:
    results: list[EvalResult] = []
    with tempfile.TemporaryDirectory(prefix="nexum-eval-") as workspace:
        runtime = NexumRuntime(workspace)

        try:
            registry = runtime.tools
            results.append(EvalResult(
                "tool_schema",
                all("parameters" in schema for schema in registry.schemas()),
                {"tool_count": len(registry.schemas())},
            ))
        except Exception as exc:
            results.append(EvalResult("tool_schema", False, {"error": str(exc)}))

        try:
            registry.validate_arguments("run_python", {"code": "print('ok')"})
            results.append(EvalResult("argument_validation", True, {}))
        except Exception as exc:
            results.append(EvalResult("argument_validation", False, {"error": str(exc)}))

        try:
            result = runtime.executor.execute(
                __import__("nexum_core.tools.executor", fromlist=["ToolCall"]).ToolCall(
                    "run_python", {"code": "print('nexum-eval-ok')"}
                )
            )
            ok = result.ok and result.output.get("exit_code") == 0 and "nexum-eval-ok" in result.output.get("stdout", "")
            results.append(EvalResult("python_execution", ok, {"output": result.output, "error": result.error}))
        except Exception as exc:
            results.append(EvalResult("python_execution", False, {"error": str(exc)}))

        try:
            registry = runtime.tools
            try:
                registry.get("read_file").execute(path="../outside.txt")
                denied = False
            except (ValueError, FileNotFoundError):
                denied = True
            results.append(EvalResult("workspace_boundary", denied, {"denied": denied}))
        except Exception as exc:
            results.append(EvalResult("workspace_boundary", False, {"error": str(exc)}))

        try:
            target = Path(workspace) / "eval.txt"
            write = runtime.executor.execute(
                __import__("nexum_core.tools.executor", fromlist=["ToolCall"]).ToolCall(
                    "write_file", {"path": str(target), "content": "roundtrip"}
                )
            )
            read = runtime.executor.execute(
                __import__("nexum_core.tools.executor", fromlist=["ToolCall"]).ToolCall(
                    "read_file", {"path": str(target)}
                )
            )
            ok = write.ok and read.ok and "roundtrip" in str(read.output)
            results.append(EvalResult("workspace_roundtrip", ok, {"write": write.output, "read": read.output}))
        except Exception as exc:
            results.append(EvalResult("workspace_roundtrip", False, {"error": str(exc)}))

    return [item.as_dict() for item in results]


def all_passed(results: list[dict]) -> bool:
    return bool(results) and all(item["ok"] for item in results)

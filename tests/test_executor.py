from nexum_core.tools.executor import ToolCall, ToolExecutor
from nexum_core.tools.workspace import build_registry

def test_executor(tmp_path):
    result = ToolExecutor(build_registry(str(tmp_path))).execute(
        ToolCall("write_file", {"path": "x.txt", "content": "ok"})
    )
    assert result.ok

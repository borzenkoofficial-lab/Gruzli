from nexum_core.runtime import NexumRuntime

def test_runtime_registers_project_and_git_tools(tmp_path):
    runtime = NexumRuntime(str(tmp_path))
    names = runtime.tools.names()
    assert "git_workspace" in names
    assert "project_lifecycle" in names

def test_project_lifecycle_inspect(tmp_path):
    runtime = NexumRuntime(str(tmp_path))
    result = runtime.tools.get("project_lifecycle").execute(operation="inspect")
    assert result["ok"] is True
    assert result["operation"] == "inspect"

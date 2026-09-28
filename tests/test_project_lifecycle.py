from pathlib import Path
from nexum_core.projects.dev_server import DevServerManager
from nexum_core.projects.templates import create_react_vite_template
from nexum_core.projects.runtime import ProjectRuntime


def test_project_runtime_inspection(tmp_path):
    create_react_vite_template(str(tmp_path))
    result = ProjectRuntime(str(tmp_path)).inspect()
    assert result.ok
    assert result.details["has_react"]


def test_dev_server_rejects_unknown_command(tmp_path):
    manager = DevServerManager(str(tmp_path))
    result = manager.start("bash", [])
    assert not result.ok
    assert result.pid is None


def test_project_lifecycle_without_install_has_steps(tmp_path):
    runtime = ProjectRuntime(str(tmp_path))
    result = runtime.lifecycle(install=False)
    assert not result["ok"]
    assert result["steps"]

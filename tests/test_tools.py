import pytest
from nexum_core.tools.workspace import WorkspaceTools

def test_workspace_boundary(tmp_path):
    ws = WorkspaceTools(str(tmp_path))
    ws.write_file("a.txt", "hello")
    assert ws.read_file("a.txt") == "hello"
    with pytest.raises(PermissionError):
        ws.read_file("../outside.txt")

from pathlib import Path

from nexum_core.projects.error_parser import ErrorParser
from nexum_core.projects.state import ProjectState


def test_error_parser_typescript():
    result = ErrorParser().parse({"stderr": "src/App.tsx:12:7: Type error"})
    assert result.category == "typescript"
    assert result.line == 12
    assert result.column == 7


def test_snapshot_restore(tmp_path):
    state = ProjectState(str(tmp_path))
    target = tmp_path / "app.txt"
    target.write_text("before", encoding="utf-8")
    snapshot = state.snapshot("before-change")
    target.write_text("after", encoding="utf-8")
    assert state.restore(snapshot.id)
    assert target.read_text(encoding="utf-8") == "before"

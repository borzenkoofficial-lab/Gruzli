from nexum_core.projects.manager import ProjectManager


def test_project_inspection(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"react":"latest","vite":"latest"}}',
        encoding="utf-8",
    )
    info = ProjectManager(str(tmp_path)).inspect()
    assert info["has_package_json"]
    assert info["has_react"]
    assert info["has_vite"]

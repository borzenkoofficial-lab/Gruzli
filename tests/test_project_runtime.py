from nexum_core.projects.templates import create_react_vite_template
from nexum_core.projects.runtime import ProjectRuntime


def test_react_template_and_inspection(tmp_path):
    created = create_react_vite_template(str(tmp_path))
    assert "package.json" in created
    info = ProjectRuntime(str(tmp_path)).inspect().details
    assert info["has_package_json"]
    assert info["has_react"]
    assert info["has_vite"]

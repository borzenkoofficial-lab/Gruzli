from nexum_core.projects.templates import create_react_vite_template
from nexum_core.projects.verifier import ProjectVerifier


def test_project_verifier_rejects_missing_manifest(tmp_path):
    report = ProjectVerifier(str(tmp_path)).verify()
    assert not report.ok
    assert report.checks


def test_project_verifier_detects_template_without_dependencies(tmp_path):
    create_react_vite_template(str(tmp_path))
    report = ProjectVerifier(str(tmp_path)).verify(build=False, test=False)
    assert report.ok is False
    assert report.checks == []

import asyncio

from nexum_core.projects.templates import create_react_vite_template
from nexum_core.projects.verifier import ProjectVerifier
from nexum_core.reasoning.state import RunManager


def test_project_verifier_rejects_missing_manifest(tmp_path):
    report = ProjectVerifier(str(tmp_path)).verify()
    assert not report.ok
    assert report.checks


def test_project_verifier_exposes_typed_python_check(tmp_path):
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    report = ProjectVerifier(str(tmp_path)).verify_python()
    assert report.ok
    assert report.checks[0]["name"] == "python_compile"


def test_run_manager_lifecycle():
    async def scenario():
        manager = RunManager()
        record = manager.create("test task")
        task = asyncio.create_task(manager.start(record.run_id, lambda: completed()))
        manager.attach(record.run_id, task)
        await task
        assert manager.get(record.run_id).status == "succeeded"
        assert any(event["kind"] == "run_finished" for event in manager.get(record.run_id).events)

    async def completed():
        return {"verified": True, "answer": "ok"}

    asyncio.run(scenario())

import pytest

from nexum_core.projects.sandbox import Sandbox


def test_sandbox_rejects_escape(tmp_path):
    sandbox = Sandbox(str(tmp_path))
    with pytest.raises(ValueError):
        sandbox.validate_path("../outside")


def test_sandbox_rejects_unknown_command(tmp_path):
    sandbox = Sandbox(str(tmp_path))
    with pytest.raises(PermissionError):
        sandbox.validate_command("bash", 10)

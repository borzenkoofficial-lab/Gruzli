from nexum_core.reasoning.verifier import Verifier

def test_verifier_rejects_failed_structured_result():
    result = Verifier().verify([{"ok": False, "error": "build failed"}], "Observable evidence confirms completion.")
    assert result.ok is False
    assert result.checks[0]["type"] == "structured_status"

def test_verifier_accepts_successful_structured_result():
    result = Verifier().verify([{"ok": True, "output": "build passed"}], "Observable evidence confirms completion.")
    assert result.ok is True

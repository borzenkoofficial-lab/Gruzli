from nexum_core.reasoning.verifier import Verifier
from nexum_core.reasoning.state import ExecutionState
from nexum_core.training.trajectory import Trajectory


def test_verifier_returns_structured_checks():
    result = Verifier().verify([{"status": "ok"}], "status ok")
    assert result.ok
    assert result.checks
    assert result.checks[0]["type"] == "content"


def test_execution_state_has_run_id_and_event_metadata():
    state = ExecutionState("demo")
    state.event("test", value=1)
    assert state.run_id
    assert state.events[0]["run_id"] == state.run_id
    assert state.events[0]["id"]
    assert state.events[0]["timestamp"]


def test_trajectory_has_run_identity():
    trajectory = Trajectory("demo")
    trajectory.record("message", {"role": "user", "content": "hi"})
    assert trajectory.run_id
    assert trajectory.messages[0]["event_id"]
    assert trajectory.messages[0]["timestamp"]

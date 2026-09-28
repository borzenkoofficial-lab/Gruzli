from nexum_core.training.preferences import from_verification, make_preference
from nexum_core.training.trajectory_store import TrajectoryStore
from nexum_core.training.trajectory import Trajectory

def test_preference_from_verification():
    item = from_verification("q", [
        {"answer": "good", "verified": True},
        {"answer": "bad", "verified": False},
    ])
    assert item["chosen"] == "good"
    assert item["rejected"] == "bad"

def test_trajectory_store(tmp_path):
    store = TrajectoryStore(str(tmp_path / "trajectories.jsonl"))
    trajectory = Trajectory("test")
    trajectory.record("verification", {"ok": True, "evidence": ["pass"]})
    store.append(trajectory)
    assert len(store.verified()) == 1

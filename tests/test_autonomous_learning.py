from nexum_core.learning.autonomous import AutonomousLearningEngine

def test_learning_engine_status_is_structured(tmp_path):
    engine = AutonomousLearningEngine(str(tmp_path))
    status = engine.status()
    assert status["trajectories"] == 0
    assert status["verified_trajectories"] == 0

def test_learning_cycle_waits_for_verified_experience(tmp_path):
    engine = AutonomousLearningEngine(str(tmp_path))
    result = engine.cycle()
    assert result.status == "waiting_for_verified_experience"
    assert result.accepted == 0

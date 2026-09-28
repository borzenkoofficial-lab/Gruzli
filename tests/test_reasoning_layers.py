from nexum_core.reasoning.critic import Critic
from nexum_core.reasoning.long_horizon import LongHorizonPlanner
from nexum_core.reasoning.world_model import WorldModel

def test_world_model_persists(tmp_path):
    path=tmp_path/"world.json"
    wm=WorldModel(str(path))
    wm.observe("Python is available", "runtime", 0.9)
    loaded=WorldModel(str(path))
    assert loaded.search("Python")[0]["confidence"] == 0.9

def test_critic_requires_verification():
    r=Critic().evaluate("task","answer",False,[])
    assert not r.accepted
    assert "verification" in " ".join(r.weaknesses)

def test_long_horizon_plan_has_verification_and_repair():
    p=LongHorizonPlanner().create("build app")
    assert any("verify" in x for x in p.steps)
    assert any("repair" in x for x in p.steps)

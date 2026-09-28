from nexum_core.agents.orchestrator import Orchestrator

def test_select_programmer():
    assert "programmer" in Orchestrator().select("implement a Python function")

def test_select_design():
    assert "designer" in Orchestrator().select("design a UI layout")

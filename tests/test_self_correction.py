from nexum_core.reasoning.self_correction import classify_failure, repair_instruction
from nexum_core.reasoning.retry import RetryBudget


def test_failure_classification():
    failure = classify_failure("Tool failed: timeout")
    assert failure.category == "timeout"
    assert failure.retryable is True
    assert "smaller" in repair_instruction(failure)


def test_retry_budget_is_bounded():
    budget = RetryBudget(max_retries=2)
    assert budget.consume("tool", "bad args")
    assert budget.consume("tool", "bad args again")
    assert not budget.consume("tool", "third attempt")
    assert budget.used == 2

from nexum_core.evals.runtime import all_passed, run_runtime_evals


def test_runtime_evals():
    results = run_runtime_evals()
    assert results
    assert all_passed(results), results

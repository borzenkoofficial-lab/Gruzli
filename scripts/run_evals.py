import json

from nexum_core.evals.runtime import all_passed, run_runtime_evals


def main() -> int:
    results = run_runtime_evals()
    print(json.dumps({"passed": all_passed(results), "results": results}, ensure_ascii=False, indent=2))
    return 0 if all_passed(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

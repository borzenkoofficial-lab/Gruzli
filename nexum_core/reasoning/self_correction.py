from dataclasses import dataclass


@dataclass
class Failure:
    category: str
    message: str
    retryable: bool = True


def classify_failure(error: str | None, verification_errors: list[str] | None = None) -> Failure:
    text = (error or " ".join(verification_errors or [])).lower()
    if "protocol" in text or "json" in text:
        return Failure("protocol", error or "invalid model protocol")
    if "timeout" in text:
        return Failure("timeout", error or "execution timeout")
    if "verification" in text or "evidence" in text:
        return Failure("verification", error or "verification failed")
    if "test" in text or "assert" in text:
        return Failure("test_failure", error or "test failure")
    if "permission" in text or "denied" in text or "unknown arguments" in text:
        return Failure("tool", error or "tool rejected the request")
    return Failure("execution", error or "execution failed")


def repair_instruction(failure: Failure) -> str:
    actions = {
        "protocol": "Return valid JSON matching the registered action schema. Do not add prose.",
        "timeout": "Reduce scope, split the operation into smaller observable actions, then retry.",
        "verification": "Inspect the actual result and perform a new verification action before finalizing.",
        "test_failure": "Inspect the failing test output, make the smallest correction, then rerun the relevant test.",
        "tool": "Check the tool schema and arguments, then choose a valid action.",
        "execution": "Inspect the error, diagnose the cause, and choose a different observable action.",
    }
    return actions.get(failure.category, actions["execution"])

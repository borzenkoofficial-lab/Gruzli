from dataclasses import dataclass
from typing import Any

@dataclass
class Verification:
    ok: bool
    evidence: list[Any]
    errors: list[str]

class Verifier:
    def verify(self, outputs: list[Any], required: str) -> Verification:
        evidence = [item for item in outputs if item is not None]
        if not evidence:
            return Verification(False, [], ['No observable execution output'])
        condition = required.lower().strip()
        if condition in ('', 'observable evidence confirms completion.', 'observable evidence confirms completion'):
            return Verification(True, evidence, [])
        normalized = ' '.join(str(item) for item in evidence).lower()
        keywords = [w.strip('.,:;()[]{}\'\"') for w in condition.split() if len(w.strip('.,:;()[]{}\'\"')) >= 4]
        missing = [w for w in keywords if w not in normalized]
        if missing:
            return Verification(False, evidence, [f'Success condition not evidenced: {required}'])
        return Verification(True, evidence, [])

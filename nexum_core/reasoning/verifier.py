from dataclasses import dataclass
from typing import Any

@dataclass
class Verification:
    ok: bool
    evidence: list[Any]
    errors: list[str]

class Verifier:
    def verify(self, outputs: list[Any], required: str) -> Verification:
        if not outputs:
            return Verification(False, [], ["No observable execution output"])
        return Verification(True, outputs, [])

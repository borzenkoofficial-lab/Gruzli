from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ParsedFailure:
    category: str
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
    evidence: list[str] | None = None


class ErrorParser:
    PATTERNS = [
        ("typescript", re.compile(r"(?P<file>[^\s()]+\.tsx?|[^\s()]+\.jsx?):(?P<line>\d+):(?P<column>\d+)")),
        ("python", re.compile(r'File "[^"]*[/\\](?P<file>[^"]+)", line (?P<line>\d+)')),
        ("npm", re.compile(r"npm ERR! (?P<msg>.+)")),
        ("test", re.compile(r"(?:FAIL|FAILED|AssertionError|assertionerror)[: ]?(?P<msg>.*)")),
        ("build", re.compile(r"(?:Build failed|build failed|error during build)[: ]?(?P<msg>.*)")),
    ]

    def parse(self, output: Any) -> ParsedFailure:
        text = str(output or "")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for category, pattern in self.PATTERNS:
            for line in lines:
                match = pattern.search(line)
                if match:
                    return ParsedFailure(
                        category=category,
                        message=match.groupdict().get("msg") or line,
                        file=match.groupdict().get("file"),
                        line=int(match.groupdict()["line"]) if match.groupdict().get("line") else None,
                        column=int(match.groupdict()["column"]) if match.groupdict().get("column") else None,
                        evidence=lines[-20:],
                    )
        return ParsedFailure("execution", lines[-1] if lines else "Unknown execution failure", evidence=lines[-20:])

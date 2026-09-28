from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Any
from ..tools.web import WebFetchTool

@dataclass
class Source:
    url: str
    title: str
    text: str
    status: int | None = None

@dataclass
class ResearchResult:
    query: str
    sources: list[dict[str, Any]]
    answer_context: str
    conflicts: list[str]

class ResearchEngine:
    def __init__(self, fetcher: WebFetchTool | None = None):
        self.fetcher = fetcher or WebFetchTool()

    def fetch(self, url: str, max_bytes: int | None = None) -> Source:
        result = self.fetcher.execute(url, max_bytes=max_bytes)
        text = re.sub(r"\s+", " ", result.get("text", "")).strip()
        title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else result["url"]
        return Source(result["url"], title[:300], text[:100000], result.get("status"))

    def build_context(self, query: str, sources: list[Source]) -> str:
        blocks = [f"SOURCE {i+1}: {s.title}\nURL: {s.url}\n{s.text[:12000]}" for i, s in enumerate(sources)]
        return f"RESEARCH QUERY: {query}\n\n" + "\n\n".join(blocks)

    def run(self, query: str, urls: list[str]) -> ResearchResult:
        sources = [self.fetch(u) for u in urls]
        conflicts = []
        if len(sources) > 1:
            for i in range(len(sources)):
                for j in range(i + 1, len(sources)):
                    if sources[i].status != sources[j].status:
                        conflicts.append(f"HTTP status differs: {sources[i].url} vs {sources[j].url}")
        return ResearchResult(query, [asdict(s) for s in sources], self.build_context(query, sources), conflicts)

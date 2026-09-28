from pathlib import Path
from .base import Tool
from .registry import ToolRegistry

class WorkspaceTool(Tool):
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def safe(self, path: str) -> Path:
        target = (self.root / path).resolve()
        target.relative_to(self.root)
        return target

class ListFiles(WorkspaceTool):
    name="list_files"; description="List files inside the workspace."
    def execute(self, path="."):
        return [str(p.relative_to(self.root)) for p in self.safe(path).rglob("*") if p.is_file()][:500]

class ReadFile(WorkspaceTool):
    name="read_file"; description="Read a UTF-8 text file."
    def execute(self, path):
        return self.safe(path).read_text(encoding="utf-8")[:100000]

class WriteFile(WorkspaceTool):
    name="write_file"; description="Write a UTF-8 text file inside the workspace."
    def execute(self, path, content):
        p=self.safe(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content, encoding="utf-8"); return {"path":str(p.relative_to(self.root))}

class SearchFiles(WorkspaceTool):
    name="search_files"; description="Search text inside workspace files."
    def execute(self, query):
        hits=[]
        for p in self.root.rglob("*"):
            if p.is_file() and len(hits)<200:
                try:
                    if query.lower() in p.read_text(encoding="utf-8", errors="ignore").lower():
                        hits.append(str(p.relative_to(self.root)))
                except OSError:
                    pass
        return hits

def build_registry(workspace="."):
    r=ToolRegistry()
    for cls in (ListFiles, ReadFile, WriteFile, SearchFiles):
        r.register(cls(workspace))
    return r

from pathlib import Path
from .base import Tool
from .registry import ToolRegistry

class WorkspaceTools:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def _path(self, relative: str) -> Path:
        target = (self.root / relative).resolve()
        if target != self.root and self.root not in target.parents:
            raise PermissionError("Path escapes workspace")
        return target

    def list_files(self, path: str = "."):
        p = self._path(path)
        return [str(x.relative_to(self.root)) for x in p.rglob("*") if x.is_file()]

    def read_file(self, path: str):
        return self._path(path).read_text(encoding="utf-8")

    def write_file(self, path: str, content: str):
        p = self._path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"path": str(p.relative_to(self.root)), "bytes": len(content.encode())}

    def search_files(self, query: str):
        hits = []
        for p in self.root.rglob("*"):
            if p.is_file() and p.stat().st_size < 2_000_000:
                try:
                    if query.lower() in p.read_text(encoding="utf-8").lower():
                        hits.append(str(p.relative_to(self.root)))
                except UnicodeDecodeError:
                    pass
        return hits

def build_registry(root: str) -> ToolRegistry:
    ws = WorkspaceTools(root)
    registry = ToolRegistry()
    registry.register(Tool("list_files", "List workspace files", ws.list_files, {"type":"object","properties":{"path":{"type":"string"}}}))
    registry.register(Tool("read_file", "Read UTF-8 text file", ws.read_file, {"type":"object","required":["path"],"properties":{"path":{"type":"string"}}}))
    registry.register(Tool("write_file", "Write UTF-8 text file", ws.write_file, {"type":"object","required":["path","content"],"properties":{"path":{"type":"string"},"content":{"type":"string"}}}))
    registry.register(Tool("search_files", "Search text across workspace", ws.search_files, {"type":"object","required":["query"],"properties":{"query":{"type":"string"}}}))
    return registry

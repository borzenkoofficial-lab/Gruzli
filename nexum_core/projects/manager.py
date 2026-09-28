from pathlib import Path


class ProjectManager:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def inspect(self) -> dict:
        files = [p for p in self.root.rglob("*") if p.is_file()]
        package = self.root / "package.json"
        pyproject = self.root / "pyproject.toml"
        return {
            "root": str(self.root),
            "file_count": len(files),
            "has_package_json": package.exists(),
            "has_pyproject": pyproject.exists(),
            "has_vite": package.exists() and "vite" in package.read_text(encoding="utf-8", errors="ignore").lower(),
            "has_react": package.exists() and "react" in package.read_text(encoding="utf-8", errors="ignore").lower(),
        }

    def create_directory(self, relative: str) -> str:
        target = (self.root / relative).resolve()
        target.relative_to(self.root)
        target.mkdir(parents=True, exist_ok=True)
        return str(target.relative_to(self.root))

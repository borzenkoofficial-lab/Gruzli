from pathlib import Path
import subprocess
from .base import Tool

class GitWorkspaceTool(Tool):
    name="git_workspace"
    description="Inspect a Git workspace."
    parameters={"type":"object","properties":{"operation":{"type":"string","enum":["clone","status","diff","log"]},"path":{"type":"string","default":"."},"repository":{"type":"string"}},"required":["operation"],"additionalProperties":False}
    def __init__(self,workspace):
        self.root=Path(workspace).resolve()
    def execute(self,operation,path=".",repository=None):
        target=(self.root/path).resolve()
        target.relative_to(self.root)
        if operation == "clone":
            if not repository or not repository.startswith("https://github.com/") or not repository.endswith(".git"):
                raise PermissionError("clone requires an HTTPS GitHub .git URL")
            if target.exists() and any(target.iterdir()):
                raise FileExistsError("clone target must be empty")
            target.parent.mkdir(parents=True, exist_ok=True)
            p=subprocess.run(["git","clone","--depth","1",repository,str(target)],cwd=self.root,capture_output=True,text=True,timeout=120)
            return {"operation":operation,"exit_code":p.returncode,"stdout":p.stdout[-20000:],"stderr":p.stderr[-10000:]}
        args={"status":["status","--short","--branch"],"diff":["diff","--stat"],"log":["log","-5","--oneline"]}[operation]
        p=subprocess.run(["git",*args],cwd=target,capture_output=True,text=True,timeout=30)
        return {"operation":operation,"exit_code":p.returncode,"stdout":p.stdout[-20000:],"stderr":p.stderr[-10000:]}

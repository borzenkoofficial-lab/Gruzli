from pathlib import Path
import subprocess
from .base import Tool

class GitWorkspaceTool(Tool):
    name="git_workspace"
    description="Inspect a Git workspace."
    parameters={"type":"object","properties":{"operation":{"type":"string","enum":["status","diff","log"]},"path":{"type":"string","default":"."}},"required":["operation"],"additionalProperties":False}
    def __init__(self,workspace):
        self.root=Path(workspace).resolve()
    def execute(self,operation,path="."):
        target=(self.root/path).resolve()
        target.relative_to(self.root)
        args={"status":["status","--short","--branch"],"diff":["diff","--stat"],"log":["log","-5","--oneline"]}[operation]
        p=subprocess.run(["git",*args],cwd=target,capture_output=True,text=True,timeout=30)
        return {"operation":operation,"exit_code":p.returncode,"stdout":p.stdout[-20000:],"stderr":p.stderr[-10000:]}

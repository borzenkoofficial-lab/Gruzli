from .runtime import ProjectRuntime
from .verifier import ProjectVerifier
from .templates import create_react_vite_template


def bootstrap_react_project(root: str) -> dict:
    created = create_react_vite_template(root)
    runtime = ProjectRuntime(root)
    return {
        "created": created,
        "inspection": runtime.inspect().details,
    }

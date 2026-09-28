CASES = [
    {"id": "health", "task": "Return the health status of the AI Core.", "expected": "ok"},
    {"id": "safety", "task": "Attempt to access a path outside the workspace.", "expected": "deny"},
    {"id": "tools", "task": "Validate a registered tool call against its schema.", "expected": "ok"},
    {"id": "python", "task": "Execute a Python snippet and verify its exit code.", "expected": "exit_code=0"},
    {"id": "roundtrip", "task": "Write a file, read it back, and verify its content.", "expected": "roundtrip"},
]

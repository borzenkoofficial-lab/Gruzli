# Security

- Workspace paths are resolved and constrained to the configured root.
- Model output is untrusted input.
- Credentials remain outside source control.
- Tool permissions must be explicit.
- Destructive operations require confirmation.
- Network access should be allowlisted.
- Training examples need provenance metadata.
- Execution and planning must remain distinguishable in traces.

The next security milestone is a sandboxed execution service for generated code.

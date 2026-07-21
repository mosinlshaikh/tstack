# Sandbox Kernel

TStack sandbox support currently creates safe subprocess plans. It does not execute commands yet.

```bash
tstack sandbox init . --output sandbox-policy.json
tstack sandbox plan sandbox-policy.json --format json --cmd python -m pytest
```

The sandbox plan enforces:

- command allowlist
- workspace boundary
- no shell metacharacters by default
- timeout requirement
- network disabled by default
- write access disabled by default
- sensitive environment marker redaction

## Boundary

This is a policy foundation, not a full OS sandbox. Future execution should run through isolated subprocesses, containers, or OS-level sandboxing while preserving this policy contract.

# Sandbox Kernel

TStack sandbox support currently creates safe subprocess plans. It does not execute commands yet.

```bash
tstack sandbox init . --output sandbox-policy.json
tstack sandbox plan sandbox-policy.json --format json --cmd python -m pytest
tstack runtime request process.run "Run tests" --format json --output request.json
tstack runtime decide request.json --approved --approver Mosin --reason "Reviewed." --format json --output decision.json
tstack sandbox run sandbox-policy.json request.json decision.json --format json --cmd python -c "print('ok')"
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

The `run` command requires an approved `process.run` runtime request. It uses a direct subprocess call with `shell=False`, a bounded timeout, redacted sensitive environment variables, and the configured workspace as the working directory.

This is controlled subprocess execution, not a full OS sandbox. Stronger isolation should later add containers, OS-level sandboxing, or separate worker identities while preserving this policy contract.

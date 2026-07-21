# SSH Automation

TStack supports safe SSH automation planning. It does not execute remote commands yet.

The goal is to make remote operations reviewable before any future execution feature exists.

## Policy

Create a project policy:

```bash
tstack ssh init .
```

This writes:

```text
.tstack/ssh-policy.json
```

The default policy is `plan-only`, requires approval, has no allowed targets, and has no allowed commands.

## Plan A Command

```bash
tstack ssh plan production-api "systemctl status app" \
  --policy .tstack/ssh-policy.json
```

JSON output:

```bash
tstack ssh plan production-api "systemctl status app" \
  --policy .tstack/ssh-policy.json \
  --format json
```

## Safety Rules

- No SSH connection is opened.
- No remote command is executed.
- Targets must be allowlisted.
- Commands must be allowlisted.
- Dangerous command patterns are blocked.
- Approval is always required.
- `execution_allowed` remains `false`.

## Future Execution Boundary

If remote execution is added later, it must require:

- Explicit user approval.
- Audit receipt.
- Secret redaction.
- No password logging.
- Host allowlist.
- Command allowlist.
- Dry-run or plan stage first.

# Runtime Kernel

The runtime kernel vertical slice is experimental and intentionally narrow.

It currently supports:

```bash
tstack workspace init .
tstack task submit --target note.txt --content "hello"
tstack kernel-approval approve TASK_ID --actor Mosin
tstack task run TASK_ID
tstack kernel-audit verify
tstack kernel-rollback apply TASK_ID
```

## What Works

- SQLite workspace state at `.tstack/state.db`
- Workspace-local approval signing key at `.tstack/approval.key`
- Deterministic task IDs
- Task persistence
- Signed approval records
- Approval replay prevention through `max_uses`
- Approved `filesystem.write` execution
- Snapshot before write
- Audit hash-chain records
- Rollback for created and overwritten files

## Current Limits

- No daemon process yet
- No task queue or worker pool yet
- No cancellation implementation yet
- No restart/resume worker recovery yet
- Only `filesystem.write` is executable in this vertical slice
- Signing is workspace-local HMAC, not asymmetric public-key approval

# Runtime Kernel

The runtime kernel vertical slice is experimental and intentionally narrow.

It currently supports:

```bash
tstack workspace init .
tstack daemon start
tstack daemon status
tstack daemon recover --policy fail
tstack task submit --target note.txt --content "hello"
tstack kernel-approval approve TASK_ID --actor Mosin
tstack task queue TASK_ID
tstack task run-next
tstack task run TASK_ID
tstack task events --task-id TASK_ID
tstack task cancel TASK_ID --reason "not needed"
tstack kernel-audit verify
tstack kernel-rollback apply TASK_ID
```

## What Works

- SQLite workspace state at `.tstack/state.db`
- Local daemon status foundation from SQLite state
- Workspace-local approval signing key at `.tstack/approval.key`
- Deterministic task IDs
- Task persistence
- Persisted task events
- Queue transition and run-next scheduler foundation
- Cancellation for non-terminal tasks
- Timeout failure path
- Restart recovery for stale `RUNNING` tasks with `fail` or `requeue` policy
- Signed approval records
- Approval replay prevention through `max_uses`
- Approved `filesystem.write` execution
- Snapshot before write
- Audit hash-chain records
- Rollback for created and overwritten files

## Current Limits

- No background daemon process yet
- No worker pool yet
- Recovery is explicit via `tstack daemon recover`; it is not automatic until a daemon loop exists
- Only `filesystem.write` is executable in this vertical slice
- Signing is workspace-local HMAC, not asymmetric public-key approval

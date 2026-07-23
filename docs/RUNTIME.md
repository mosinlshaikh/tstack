# Runtime Kernel

The runtime kernel vertical slice is experimental and intentionally narrow.

It currently supports:

```bash
tstack workspace init .
tstack workspace export --output state-bundle.json
tstack workspace import state-bundle.json --workspace restored-workspace
tstack daemon start
tstack daemon status
tstack daemon recover --policy fail
tstack daemon run --cycles 1 --interval-seconds 0
tstackd --workspace . --cycles 1 --interval-seconds 0
tstack task submit --target note.txt --content "hello"
tstack kernel-approval approve TASK_ID --actor Mosin
tstack kernel-approval revoke APPROVAL_ID --actor Mosin --reason "No longer approved"
tstack task queue TASK_ID
tstack task run-next
tstack task run TASK_ID
tstack task events --task-id TASK_ID
tstack task cancel TASK_ID --reason "not needed"
tstack task retry TASK_ID --reason "transient failure fixed"
tstack worker run --workers 2
tstack benchmark kernel --tasks 100 --workers 4 --output benchmark.json
tstack kernel-audit verify
tstack kernel-rollback apply TASK_ID
```

## What Works

- SQLite workspace state at `.tstack/state.db`
- Local daemon status foundation from SQLite state
- Foreground daemon loop with SQLite lease and heartbeat records
- Portable workspace state export/import without approval key material
- Workspace-local approval signing key at `.tstack/approval.key`
- Deterministic task IDs
- Task persistence
- Persisted task events
- Queue transition and run-next scheduler foundation
- Cancellation for non-terminal tasks
- Failed or blocked task retry back to approval review
- Timeout failure path
- Restart recovery for stale `RUNNING` tasks with `fail` or `requeue` policy, invoked by daemon startup
- Same-process bounded worker pool simulation over queued tasks
- Machine-readable local kernel benchmark
- Signed approval records
- Approval replay prevention through `max_uses`
- Approval expiry enforcement
- Approval revocation
- Approved `filesystem.write` execution
- Snapshot before write
- Audit hash-chain records
- Rollback for created and overwritten files

## Current Limits

- No installed OS background service yet
- Daemon mode is foreground and cooperative; process supervision belongs to the host for now
- Worker command is same-process simulation, not distributed execution
- Only `filesystem.write` is executable in this vertical slice
- Signing is workspace-local HMAC, not asymmetric public-key approval
- Imported approvals cannot be verified with the original key unless key custody is separately handled; the export intentionally excludes key material

Retry does not bypass approval. A retried task returns to `WAITING_FOR_APPROVAL`, and queueing it again requires a valid non-expired, non-revoked approval with remaining uses.

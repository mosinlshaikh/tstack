# Persistent Task Runtime

Status: **experimental foundation**

TStack now has a restart-safe SQLite task lifecycle independent of any one CLI process. This is the first persistence layer required for a future local daemon and bounded worker pool.

## Implemented guarantees

- Tasks are stored in SQLite WAL mode with `synchronous=FULL`.
- Submission normalizes JSON parameters and assigns deterministic lifecycle metadata.
- Queue ordering is priority-first and then FIFO by creation time.
- Worker leasing is atomic under `BEGIN IMMEDIATE`.
- Only the lease owner can heartbeat or finish a running task.
- Running cancellation is cooperative through `CANCEL_REQUESTED`.
- Queued cancellation is immediate.
- Failed tasks requeue only while their attempt budget remains.
- Expired worker leases are recovered after process restart.
- Concurrent workers cannot lease the same queued task.

## State model

```text
CREATED
  -> QUEUED
  -> BLOCKED
  -> CANCELLED

QUEUED
  -> RUNNING
  -> BLOCKED
  -> CANCELLED

RUNNING
  -> SUCCEEDED
  -> FAILED
  -> RETRYING -> QUEUED
  -> CANCEL_REQUESTED -> CANCELLED
  -> BLOCKED
```

Terminal states are `SUCCEEDED`, `FAILED`, and `CANCELLED`.

## Security boundary

The task runtime schedules logical work only. It does not grant OS permissions and must not execute a capability directly. A worker must still create or load the exact action request, validate the signed approval, consume it atomically, and route the action through the capability broker/secure execution layer.

## Restart recovery

On startup, a daemon or worker supervisor should call `recover_expired_leases()`. Tasks with remaining attempts return to `QUEUED`; exhausted tasks become `FAILED`; cancellation-requested tasks become `CANCELLED`.

## Not implemented yet

- Long-running daemon/service process
- IPC or local HTTP API
- Event streaming
- Worker heartbeat loop
- Capability-broker dispatch integration
- Task dependencies/DAGs
- Dead-letter queue
- Per-task CPU, memory, and process quotas
- OS/container isolation

These must be implemented before Runtime Kernel v1 can be declared complete.

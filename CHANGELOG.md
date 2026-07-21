# Changelog

## 0.18.0a1 - Unreleased

- Added SQLite-backed runtime kernel vertical slice.
- Added persisted task events, queue transition, run-next scheduler foundation, cancellation, and timeout failure path.
- Added daemon start/status foundation backed by SQLite workspace health, queue counts, and audit validation.
- Added explicit restart recovery for stale `RUNNING` tasks with fail/requeue policies.
- Added same-process bounded worker pool simulation for queued tasks.
- Added public capability model registry with honest status labels.
- Added signed approval expiry validation and approval revocation.
- Added signed task approvals using workspace-local HMAC keys.
- Added task persistence, approved filesystem write execution, snapshots, audit-chain records, and rollback.
- Added controlled sandbox runner bound to runtime approval.
- Added tamper-evident runtime audit log and transactional file runtime.

## 0.17.0 - Alpha

- Added engineering knowledge packs, agent planning, runtime capability requests, sandbox planning, file runtime, and release-governance foundations.

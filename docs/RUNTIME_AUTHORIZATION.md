# Runtime Authorization Integrity

Status: **experimental foundation**

TStack runtime authorization must approve the exact action that will execute, not only a generic capability name.

## Guarantees introduced in `0.18.0a1`

- Canonical action parameters are included in every request.
- A SHA-256 `parameters_hash` binds the request to those exact parameters.
- The complete request has its own `request_hash` and nonce.
- Human decisions are signed with Ed25519.
- Approvals have issue and expiry timestamps.
- Runtime v1 approvals are single-use only.
- SQLite stores requests and approvals transactionally.
- Atomic consumption prevents the same approval from authorizing two executions.
- Signed sandbox and file-plan bindings reject modified payloads.
- Durable execution journal entries are fsynced before and after actions.
- Completed receipts receive a SHA-256 result digest.
- Journal hash chaining detects modification, deletion, or reordering.

## Required verification order

```text
request schema
→ request hash
→ parameters hash
→ request/approval identity
→ nonce
→ approval scope
→ expiry
→ Ed25519 signature
→ SQLite single-use consumption
→ durable started journal event
→ execution
→ completed/failed journal event
→ result hash verification
```

## Key storage boundary

`generate_signing_keypair()` exists for tests and bootstrap tooling. Production private keys must be stored through an operating-system credential vault:

- Windows Credential Manager
- macOS Keychain
- Linux Secret Service

Private keys must never be committed, written to audit output, or included in approval JSON.

## Current secure execution APIs

- `execute_signed_sandbox()` binds command, arguments, working directory, timeout, write scope, and network intent.
- `execute_signed_file_plan()` binds the complete organize plan, root, and dry-run state.
- `execute_with_journal()` requires durable started/completed/failed events around a secure operation.
- `verify_execution_journal()` validates journal order and hash-chain integrity.

## Remaining boundaries

1. Existing legacy CLI execution paths still require migration to the signed contract.
2. The current subprocess runner is controlled execution, not full OS/container isolation.
3. Network and write restrictions must distinguish declared policy from OS-enforced isolation.
4. File transactions still need a persistent per-move recovery journal for process-crash recovery.
5. Production signing keys still require OS credential-vault adapters.
6. Cross-process concurrency and full Python-version CI must pass before merge.

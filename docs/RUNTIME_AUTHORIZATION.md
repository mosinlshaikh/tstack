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
→ execution
→ automatic audit append
```

The current branch implements request creation, signature verification, persistence, and single-use consumption. Existing sandbox and file executors are **not yet migrated** to this v1 authorization contract; they must not be described as fully protected by signed approvals until that integration is complete.

## Key storage boundary

`generate_signing_keypair()` exists for tests and bootstrap tooling. Production private keys must be stored through an operating-system credential vault:

- Windows Credential Manager
- macOS Keychain
- Linux Secret Service

Private keys must never be committed, written to audit output, or included in approval JSON.

## Next integration slice

1. Bind `sandbox run` to `ActionRequest.parameters` containing executable, arguments, working directory, timeout, network, write scope, and permitted environment keys.
2. Bind file transactions to an immutable plan hash and source metadata.
3. Verify the signature immediately before execution.
4. Consume approval atomically before the first side effect.
5. Append execution and rollback events automatically to the audit chain.
6. Add crash-safe transaction journals and recovery.

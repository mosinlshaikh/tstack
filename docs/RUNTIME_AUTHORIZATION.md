# Runtime Authorization Integrity

Status: **experimental secure execution foundation**

TStack runtime authorization approves the exact action that will execute, not only a generic capability name.

## Guarantees introduced in `0.18.0a1`

- Canonical action parameters are included in every request.
- A SHA-256 `parameters_hash` binds the request to those exact parameters.
- The complete request has its own `request_hash` and nonce.
- Human decisions are signed with Ed25519.
- Approvals have issue and expiry timestamps.
- Runtime v1 approvals are single-use only.
- SQLite stores requests and approvals transactionally.
- Atomic consumption prevents the same approval from authorizing two executions.
- Sandbox execution is bound to command, cwd, timeout, write, and network parameters.
- File execution is bound to the complete organize plan, resolved root, and dry-run/apply mode.
- Durable execution journals record lifecycle state and result hashes.
- `tstack-secure` exposes the signed execution path without pretending legacy commands are equivalent.

## Secure CLI

```text
tstack-secure sandbox-run POLICY REQUEST APPROVAL PUBLIC_KEY RUNTIME_DB --cmd python -m pytest
tstack-secure file-run PLAN REQUEST APPROVAL PUBLIC_KEY RUNTIME_DB
tstack-secure file-run PLAN REQUEST APPROVAL PUBLIC_KEY RUNTIME_DB --apply --manifest transaction.json
```

The public key file may contain 32 raw Ed25519 bytes or base64-encoded raw bytes. Private signing keys must remain in an operating-system credential vault.

## Verification order

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
→ durable execution journal
```

## Security boundaries

- `tstack-secure` is the preferred execution entrypoint for Runtime Authorization v1.
- Existing legacy CLI paths remain compatibility-only and are not equivalent to signed authorization.
- Controlled subprocess execution is not full OS/container isolation.
- A declared `network=false` is not an enforced network sandbox until OS/container controls exist.
- Production key generation and storage still require OS credential-vault integration.
- Full interrupted file-transaction recovery requires per-move durable checkpoints and recovery tooling.
- The branch must not be promoted until the complete test matrix is green.

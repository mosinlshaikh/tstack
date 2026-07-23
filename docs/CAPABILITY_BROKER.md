# Capability Broker v1

Status: **experimental secure runtime foundation**

The Capability Broker is the only runtime component permitted to map a logical task to a capability handler. Agents, hosts and the daemon must not call operating-system tools directly.

## Dispatch path

```text
persistent task
→ capability lookup
→ definition validation
→ policy evaluation
→ exact-parameter decision hash
→ registered handler
→ result receipt
```

## Fail-closed guarantees

- Unknown capabilities are denied.
- Duplicate capability registration is rejected.
- High and critical risk definitions require approval.
- Policy-approved capabilities without handlers fail closed.
- Decision receipts bind the task's canonical parameters with SHA-256.
- The bootstrap policy pre-authorizes only `runtime.noop`.
- Operational capabilities remain denied until a dedicated secure policy adapter verifies exact signed authorization and sandbox requirements.

## Bootstrap registry

The daemon currently exposes definitions for:

- `runtime.noop`
- `process.run`
- `filesystem.move`
- `browser.navigate`
- `docker.run`
- `git.commit`
- `deployment.publish`

Only `runtime.noop` has an executable handler in the bootstrap broker. The remaining definitions exist for discovery and policy reporting and are intentionally denied.

## CLI

```text
tstackd capabilities
```

prints the daemon's current capability definitions.

## Security boundary

The broker is not an approval signer, sandbox or operating-system privilege boundary by itself. An operational policy adapter must verify:

1. exact action request and parameter hash
2. Ed25519 approval signature
3. nonce, expiry and scope
4. atomic single-use approval consumption
5. required sandbox plan
6. audit and rollback configuration

before returning an allow decision.

## Remaining work

- Connect signed `process.run` and `filesystem.move` adapters.
- Persist broker decisions in the execution audit chain.
- Add workspace and agent policy overlays.
- Add plugin capability manifests and isolation.
- Add rootless-container enforcement for untrusted execution.
- Add broker metrics and policy-denial counters.

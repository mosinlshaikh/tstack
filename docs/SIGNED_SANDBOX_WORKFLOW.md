# Signed Capability Broker → Rootless Sandbox Workflow

Status: **experimental end-to-end secure execution slice**

This milestone connects the persistent task model, Capability Broker, Ed25519 approval layer, atomic single-use approval store, rootless Docker sandbox, and durable execution journal.

## Execution path

```text
Persistent docker.run task
→ exact SandboxRequest
→ ActionRequest with sandbox parameters
→ Ed25519 SignedApproval
→ Capability Broker policy decision
→ atomic approval consumption
→ rootless Docker sandbox
→ artifact collection
→ hash-chained started/completed/failed audit events
→ workflow receipt
```

## Exact approval boundary

The signed request binds:

- container image
- complete argument-array command
- resolved workspace
- complete sandbox profile
- environment variables
- artifact paths
- sandbox identifier
- sandbox request hash
- task workspace and capability

Changing any one of these values creates a different parameter hash and is rejected before sandbox execution.

## Replay protection

The broker consumes the registered approval in SQLite before invoking Docker. A second dispatch with the same request is rejected and cannot invoke the executor.

## Audit behavior

A `started` journal event is fsynced after approval consumption and before execution. The adapter then appends either:

- `completed`, including a digest of the sandbox receipt; or
- `failed`, including the bounded exception type and message.

## Test strategy

The deterministic end-to-end tests inject a fake sandbox executor. This validates task binding, policy, signature verification, single-use consumption, replay rejection, command tampering rejection, and journal integrity without requiring Docker in the generic Python matrix.

A separate Docker-enabled integration job is still required to validate real rootless isolation, network denial, resource limits, timeout cleanup, and artifact collection.

## Production boundary

This slice is not production complete until:

- the complete Python CI matrix is green;
- a rootless-Docker integration job is green;
- image references are digest pinned;
- trusted key storage and rotation are implemented;
- daemon workers load signed execution material through a protected local API rather than direct file paths;
- journal heads are externally signed or anchored.

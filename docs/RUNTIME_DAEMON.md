# TStack Runtime Daemon

Status: **experimental Phase 2 foundation**

`tstackd` is the persistent local supervisor for the SQLite task runtime. It provides bounded worker execution, atomic task leasing, startup recovery, heartbeats, durable health status, cooperative stop requests, and graceful shutdown.

## Commands

```text
tstackd --database .tstack/runtime/tasks.db --state-dir .tstack/runtime/daemon run --workers 2
tstackd --database .tstack/runtime/tasks.db submit runtime.noop "Acknowledge task" --parameters '{"value": 1}'
tstackd --database .tstack/runtime/tasks.db tasks
tstackd --state-dir .tstack/runtime/daemon status
tstackd --state-dir .tstack/runtime/daemon stop
```

`run` remains a foreground process. Operating-system service installation is intentionally deferred until the daemon protocol and Capability Broker stabilize.

## Lifecycle

```text
startup
→ recover expired leases
→ publish STARTING status
→ start bounded workers
→ publish RUNNING status
→ lease / heartbeat / finish tasks
→ receive signal or stop.request
→ publish STOPPING
→ join workers
→ publish STOPPED
```

## Guarantees

- Worker count is bounded and validated.
- Workers lease tasks through SQLite, never through an in-memory-only queue.
- Each active task receives a heartbeat thread while dispatch is running.
- Startup calls `recover_expired_leases()` before accepting new work.
- SIGINT and SIGTERM request graceful shutdown when running in the main thread.
- A file-based stop request works across local processes.
- Status is replaced atomically through a temporary file.
- Task failures are persisted through the existing retry/failure lifecycle.
- The daemon never executes arbitrary operational capabilities directly.

## Security boundary

The bundled bootstrap dispatcher accepts only `runtime.noop`. Any filesystem, process, browser, Git, Docker, Blender, mobile-build, network, or deployment capability is denied until Capability Broker v1 verifies policy, exact signed authorization, and sandbox requirements.

This separation is intentional:

```text
Task Runtime
→ Runtime Daemon
→ Capability Broker (next phase)
→ Signed Authorization
→ Sandbox / Native Adapter
→ Audit
```

## Not yet included

- Capability Broker dispatch
- authenticated IPC or local HTTP API
- OS service installers
- event streaming
- process-level worker isolation
- CPU and memory enforcement
- rootless container sandbox
- distributed workers
- task dependencies / DAG execution

Phase 2 is complete only as a **local daemon foundation** after the Python 3.10/3.11/3.12 CI matrix is green. It is not the complete production runtime until the next broker and sandbox phases are implemented.

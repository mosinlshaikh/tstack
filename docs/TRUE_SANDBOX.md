# True Sandbox v1

Status: **experimental rootless Docker foundation**

TStack now provides a structured container sandbox for generated or otherwise untrusted command workloads.

## Default security posture

- Docker rootless mode is required and verified before execution.
- Containers are never privileged.
- The Docker socket is never mounted.
- All Linux capabilities are dropped.
- `no-new-privileges` is enabled.
- The container root filesystem is read-only.
- `/tmp` is a bounded temporary filesystem.
- The workspace is the only host path mounted.
- Networking is disabled by default.
- CPU, memory and process limits are mandatory.
- Commands are argument arrays and never shell strings.
- Timeout cleanup force-removes the named container.
- Sensitive host environment variables are rejected.

## Profiles

- `restricted`: 1 CPU, 512 MiB, 128 processes, 120 seconds, no network.
- `test`: 2 CPUs, 1 GiB, 256 processes, 600 seconds, no network.
- `build`: 2 CPUs, 2 GiB, 256 processes, 900 seconds, no network.

Profiles are validated before a Docker command is generated.

## CLI

```bash
tstack-sandbox doctor
tstack-sandbox profiles
tstack-sandbox plan python:3.12-slim --workspace . --profile test --cmd python -m pytest
tstack-sandbox run python:3.12-slim --workspace . --profile test --artifact report.xml --cmd python -m pytest --junitxml=report.xml
```

`plan` is safe and does not start a container. `run` first verifies that Docker reports rootless mode.

## Capability Broker boundary

The container runtime does not grant authorization. A production `process.run` or `docker.run` task must still carry an exact signed approval and be admitted by the Capability Broker before `execute_sandbox()` is called.

## Current limitations

- Linux Docker rootless mode is the first supported enforcement backend.
- AppArmor and custom seccomp profiles are not yet distributed by TStack; Docker defaults remain active in addition to capability dropping and no-new-privileges.
- Disk quota enforcement depends on the host storage driver.
- Network allow-list mode is not implemented; only `none` and Docker `bridge` exist, with `none` as the default.
- Container image provenance and digest pinning are not yet mandatory.
- Docker-backed integration tests require an explicitly configured rootless Docker runner and are not assumed on generic CI hosts.

Do not describe this phase as production complete until image digest policy, signed broker integration, Docker-backed isolation tests, and all CI jobs are green.

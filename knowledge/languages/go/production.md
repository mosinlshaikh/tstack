# Go Production

Go production systems benefit from simple binaries, explicit runtime controls, and strong operational discipline.

## Runtime

Production projects should declare:

- Go version.
- Build command.
- Service entry point.
- Runtime configuration.
- Deployment target.

## Operations

Services should include:

- Health checks.
- Structured logs.
- Metrics.
- Timeouts and cancellation.
- Graceful shutdown.
- Resource limits.

## Release Readiness

Before release, verify:

- `go test ./...` passes.
- Static analysis or `go vet` passes.
- `go.sum` is present for modules.
- Build artifact is generated from a known commit.
- SBOM and checksums exist for official releases.
- Rollback path is documented.

## TStack Production Signals

TStack should increase risk when:

- Go version is undeclared.
- CI is missing.
- Tests are absent.
- Runtime configuration is undocumented.
- Release artifacts cannot be verified.

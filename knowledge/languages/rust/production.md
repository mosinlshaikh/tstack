# Rust Production

Production Rust systems need clear build, toolchain, observability, and release controls.

## Runtime

Production projects should declare:

- Rust version or toolchain.
- Build command.
- Binary or library targets.
- Runtime configuration.
- Deployment target.

## Operations

Services should include:

- Structured logs.
- Metrics.
- Health checks.
- Graceful shutdown.
- Timeouts and cancellation where applicable.
- Clear panic strategy for production.

## Release Readiness

Before release, verify:

- `cargo test` passes.
- Static analysis passes.
- Formatting passes.
- `Cargo.lock` is committed for applications.
- Build artifact is generated from a known commit.
- SBOM and checksums exist for official releases.
- Unsafe usage has review evidence where applicable.

## TStack Production Signals

TStack should increase risk when:

- Toolchain version is undeclared.
- CI is missing.
- Tests are absent.
- `Cargo.lock` is missing for an application.
- Release artifacts cannot be verified.

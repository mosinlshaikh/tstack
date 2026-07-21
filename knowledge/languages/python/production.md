# Python Production

Production Python systems need disciplined packaging, configuration, observability, and release controls.

## Runtime

Production projects should declare:

- Supported Python versions.
- Application entry points.
- Runtime dependencies.
- Deployment target.
- Environment configuration model.

## Packaging

Recommended practices:

- Prefer `pyproject.toml` for modern packaging metadata.
- Keep build configuration explicit.
- Separate library code from scripts.
- Use reproducible dependency resolution for deployed applications.
- Build artifacts in clean environments.

## Configuration

Configuration should be:

- Environment-specific.
- Validated at startup.
- Safe to log only after redaction.
- Documented for operators.

Secrets should not be committed and should not be printed.

## Observability

Production services should expose:

- Structured logs.
- Health checks.
- Error reporting.
- Metrics for throughput, latency, failures, and resource use.
- Traceability for important external calls where practical.

## Release Readiness

Before release, verify:

- Tests pass in CI.
- Dependency strategy is reproducible.
- Security review has no unresolved critical findings.
- Build artifact is generated from a known commit.
- SBOM and checksums exist for official releases.
- Rollback path is documented for service deployments.

## TStack Production Signals

TStack should increase risk when:

- Python version support is undeclared.
- CI is missing.
- Build metadata is missing.
- Dependency lock strategy is unclear.
- Runtime configuration is undocumented.
- Release artifacts cannot be verified.

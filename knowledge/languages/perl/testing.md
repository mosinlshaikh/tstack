# Perl Testing

Testing strategy for Perl should cover fast unit checks, integration boundaries, and release-critical workflows.

## Test layers

- Unit tests for pure logic and edge cases.
- Integration tests for databases, files, network clients, and framework wiring.
- Contract tests for APIs and plugin boundaries.
- Security regression tests for previously fixed vulnerabilities.
- Smoke tests for packaged or deployed artifacts.

## CI requirements

CI should install dependencies reproducibly, run formatting or linting where available, execute tests, and publish machine-readable failure output.

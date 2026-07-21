# Go Testing

Go has strong built-in testing support. Production projects should use it consistently.

## Test Layers

Recommended layers:

- Unit tests with `testing`.
- Table-driven tests for input/output behavior.
- Integration tests for databases and external services.
- Race tests for concurrent code.
- Benchmarks for performance-critical code.

## Quality Signals

Healthy Go projects usually include:

- `*_test.go` files near relevant packages.
- CI running `go test ./...`.
- `go vet` or equivalent static checks.
- Regression tests for fixed defects.
- Clear test strategy for concurrency behavior.

## Test Data

Use synthetic fixtures and avoid real credentials. Tests should not depend on hidden local services unless clearly marked as integration tests.

## TStack Testing Rules

TStack should flag:

- No `*_test.go` files.
- Tests not wired into CI.
- Missing race testing for concurrency-heavy modules.
- No benchmark evidence for performance-critical paths.

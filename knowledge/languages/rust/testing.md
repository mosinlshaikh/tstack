# Rust Testing

Rust testing should protect correctness, safety boundaries, and release-critical behavior.

## Test Layers

Recommended layers:

- Unit tests inside modules.
- Integration tests under `tests/`.
- Property tests for parsers and stateful logic where useful.
- Fuzz tests for untrusted input boundaries where risk justifies it.
- Benchmarks for performance-sensitive code.

## Quality Signals

Healthy Rust projects usually include:

- `cargo test` in CI.
- `cargo clippy` or equivalent static analysis.
- Formatting checks.
- Tests around unsafe and FFI boundaries.
- Regression tests for fixed defects.

## Test Data

Use synthetic test data and avoid real credentials. Fuzz corpora should not contain sensitive samples.

## TStack Testing Rules

TStack should flag:

- No tests.
- Tests not wired into CI.
- Unsafe code without focused tests.
- Missing regression tests after high-risk fixes.
- Missing benchmark evidence for claimed performance work.

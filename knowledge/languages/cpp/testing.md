# C++ Testing

C++ projects need tests plus static and dynamic safety checks.

## Test Layers

- Unit tests.
- Integration tests.
- ABI or compatibility tests where needed.
- Sanitizer runs.
- Fuzz tests for parsers and untrusted input.
- Benchmarks for performance-critical code.

TStack should flag missing tests, missing sanitizer plan, and unsafe code paths without targeted coverage.

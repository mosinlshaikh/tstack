# C Testing

C projects need tests plus tool-assisted safety checks.

## Test Layers

- Unit tests.
- Integration tests.
- Fuzz tests for untrusted input.
- Sanitizer runs.
- Platform-specific smoke tests.

TStack should flag missing tests, missing sanitizer strategy, and parser/network code without fuzzing evidence.

# Kotlin Testing

Kotlin projects should cover domain logic, coroutine behavior, platform boundaries, and release-critical flows.

## Test Layers

- Unit tests.
- Coroutine tests.
- Integration tests.
- Android instrumentation tests where applicable.
- Regression tests for fixed defects.

TStack should flag missing unit tests, missing instrumentation tests for Android-critical paths, and coroutine-heavy code without focused tests.

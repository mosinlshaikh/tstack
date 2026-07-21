# Swift Testing

Swift projects should test domain logic, platform boundaries, UI-critical behavior, and release-critical flows.

## Test Layers

- Unit tests.
- Integration tests.
- UI tests where applicable.
- Regression tests for fixed defects.
- Platform-specific smoke tests.

TStack should flag missing tests, missing CI test execution, and untested platform permission or storage behavior.

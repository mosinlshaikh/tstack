# Python Testing

Python projects should use tests to protect behavior, interfaces, and release decisions.

## Test Layers

Recommended layers:

- Unit tests for deterministic logic.
- Integration tests for databases, filesystems, services, and framework boundaries.
- Contract tests for API and message formats.
- Regression tests for fixed defects.
- Smoke tests for CLI or service startup.

## Test Tooling

Common tools:

- `pytest` for test execution.
- `unittest` for standard-library test support.
- `coverage.py` for coverage measurement.
- `tox` or `nox` for multi-environment checks.
- Static analysis tools such as `ruff`, `mypy`, or equivalent project choices.

## Quality Signals

Healthy Python projects usually have:

- Tests committed with source.
- CI running tests.
- Tests covering high-risk paths.
- Regression tests for security or release defects.
- Deterministic tests that do not depend on hidden local state.

## Test Data

Test data should avoid real secrets and personal data. Use synthetic fixtures where possible.

## TStack Testing Rules

TStack should flag Python projects with:

- No tests.
- Tests not wired into CI.
- Missing smoke tests for CLI tools.
- Missing regression tests after high-risk fixes.
- No clear test strategy for release-critical behavior.

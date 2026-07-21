# Haskell Production

Production readiness for Haskell requires clear build, release, runtime, and rollback contracts.

## Readiness checklist

- Version and runtime requirements are documented.
- Build and dependency installation are reproducible.
- Configuration is externalized and secrets are managed outside source control.
- Logs, metrics, and error reporting are available.
- Rollback and recovery steps are documented.
- Ownership, support boundaries, and operational runbooks are clear.

## TStack expectation

A Haskell project should not be marked production-ready until tests, security checks, documentation, and release verification all pass.

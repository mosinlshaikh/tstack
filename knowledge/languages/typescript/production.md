# TypeScript Production

Production TypeScript needs reproducible builds, runtime validation, dependency controls, and target-specific observability.

## Required Signals

- `package.json` scripts for build, test, and typecheck.
- Lockfile committed.
- TypeScript config present.
- Production build verified in CI.
- Environment variables documented and secret-safe.
- Release artifact or deployment path documented.

TStack should increase risk when build output, runtime validation, or dependency controls are unclear.

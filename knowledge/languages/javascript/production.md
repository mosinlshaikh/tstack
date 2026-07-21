# JavaScript Production

Production JavaScript requires reproducible dependency installation, runtime validation, observability, and deployment clarity.

## Required Signals

- `package.json` scripts for test and build where applicable.
- Lockfile committed.
- Runtime version strategy.
- Production build or deployment path documented.
- Environment variables documented and secret-safe.

TStack should increase risk when dependency controls, runtime validation, or production build evidence are unclear.

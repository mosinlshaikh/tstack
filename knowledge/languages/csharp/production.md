# C# Production

Production C# systems need explicit runtime, configuration, observability, and release controls.

## Required Signals

- Target framework declared.
- Build and publish path documented.
- Tests run in CI.
- Configuration and secrets model documented.
- Health checks, metrics, and structured logs for services.

TStack should increase risk when runtime version, deployment target, or dependency controls are unclear.

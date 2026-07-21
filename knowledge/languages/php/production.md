# PHP Production

Production PHP requires version constraints, dependency control, server configuration, and release discipline.

## Required Signals

- PHP version constraint.
- `composer.lock` for applications.
- Tests run in CI.
- Environment and secret model documented.
- Server/runtime configuration documented.

TStack should increase risk when Composer, runtime, or deployment controls are unclear.

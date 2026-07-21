# TypeScript Security

TypeScript security depends on runtime validation, dependency hygiene, browser security, and backend input controls.

## High-Risk Patterns

- Trusting TypeScript types for external input without runtime validation.
- XSS through unsafe HTML rendering.
- Secrets exposed in frontend bundles.
- SQL or shell command string construction.
- Insecure token storage.
- Dependency lockfile missing.

TStack should mark leaked secrets, unsafe frontend exposure, or missing dependency controls as high risk.

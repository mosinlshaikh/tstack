# Python Security

Python security depends on safe dependency management, careful input handling, avoiding dangerous dynamic features, and protecting secrets.

## High-Risk Patterns

Treat these as high risk unless evidence proves they are controlled:

- `eval()` or `exec()` on untrusted input.
- Unsafe deserialization with `pickle`, `marshal`, or unsafe YAML loaders.
- Shell execution with interpolated user input.
- Hardcoded secrets, tokens, private keys, or credentials.
- SQL built through string concatenation.
- Debug mode enabled in production.
- Broad filesystem access from untrusted paths.

## Dependency Security

Recommended controls:

- Use pinned or lockfile-backed dependencies for deployable applications.
- Review dependency update diffs.
- Run dependency vulnerability scanning in CI where available.
- Avoid abandoned packages for security-sensitive paths.
- Separate application dependencies from development-only tools.

## Input Handling

Applications should validate:

- Request payloads.
- File uploads.
- Path inputs.
- Environment-derived configuration.
- Data crossing service boundaries.

Prefer framework validation, typed schemas, and explicit allowlists over ad hoc checks.

## Secrets

Secrets must not live in source control.

Required practices:

- Load secrets from a secret manager or protected runtime environment.
- Keep `.env` files out of commits.
- Redact secret values from logs.
- Rotate secrets after exposure.
- Use least-privilege credentials.

## TStack Security Signals

TStack should flag:

- Credential-like values.
- `.env` files in repository scope.
- Missing `SECURITY.md`.
- Missing dependency lock or resolution strategy.
- Dangerous dynamic execution patterns when scanner support exists.

Security findings should include remediation steps without exposing secret values.

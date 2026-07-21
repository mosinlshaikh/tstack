# Go Security

Go security depends on dependency hygiene, careful network boundaries, context handling, and safe input processing.

## High-Risk Patterns

Review carefully:

- Shell execution with untrusted arguments.
- SQL built through string concatenation.
- HTTP clients without timeouts.
- Servers without request limits.
- Secrets committed in source.
- Unsafe path joins for user-controlled file paths.
- Broad use of `unsafe`.

## Dependency Security

Recommended controls:

- Commit `go.sum` for modules.
- Review major dependency updates.
- Prefer maintained packages for security-sensitive code.
- Keep generated code and vendored code clearly separated.

## Network Controls

Production services should define:

- Timeouts.
- Context cancellation.
- Request size limits.
- TLS expectations.
- Authentication and authorization boundaries.

## TStack Security Signals

TStack should flag:

- Missing `go.sum`.
- Credential-like values.
- Missing security policy.
- Unbounded network operations when detectable.
- Use of `unsafe` in security-sensitive areas when scanner support exists.

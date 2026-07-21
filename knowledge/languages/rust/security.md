# Rust Security

Rust prevents many memory-safety defects by default, but secure Rust still requires dependency, unsafe-code, input, and cryptography discipline.

## High-Risk Patterns

Review carefully:

- `unsafe` blocks.
- FFI boundaries.
- Manual memory or pointer handling.
- Cryptographic implementations.
- Parsing of untrusted data.
- Shell execution or filesystem access from untrusted input.
- Secrets in source or logs.

## Unsafe Code

Unsafe code should have:

- Clear justification.
- Tight scope.
- Invariant documentation.
- Tests around boundary behavior.
- Review by someone who understands the safety contract.

## Dependency Security

Recommended controls:

- Commit `Cargo.lock` for applications.
- Review dependency updates.
- Avoid unmaintained crates for sensitive paths.
- Use vulnerability scanning where available.

## TStack Security Signals

TStack should flag:

- Credential-like values.
- Missing `Cargo.lock` for applications.
- Missing security policy.
- Unsafe usage when scanner support exists.
- Release artifacts without provenance or checksums.

# COBOL Testing

Testing for COBOL should prove behavior at the right level: fast logic tests, integration checks, and release smoke tests.

## Required layers

- Unit tests for deterministic logic and edge cases.
- Integration tests for storage, network, operating-system, and framework boundaries.
- Contract tests for public APIs, plugins, CLIs, or smart contracts where relevant.
- Security regression tests for previous findings.
- CI checks that run consistently on supported platforms.

## Evidence rule

A COBOL project is not production-ready without automated tests tied to the critical workflows it claims to support.

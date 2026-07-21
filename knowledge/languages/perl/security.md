# Perl Security

Security guidance for Perl projects should start with dependency trust, input validation, secrets handling, and deployment boundaries.

## Required practices

- Never commit secrets, tokens, private keys, or environment files.
- Validate and normalize all untrusted input at system boundaries.
- Use maintained libraries for cryptography, authentication, parsing, and network protocols.
- Pin or lock dependencies where the ecosystem supports it.
- Run security checks in CI and review high-risk changes manually.

## Review focus

- Injection risks.
- Unsafe deserialization or dynamic evaluation.
- Path traversal and file permission errors.
- Weak authentication, authorization, and session handling.
- Supply-chain drift and abandoned dependencies.

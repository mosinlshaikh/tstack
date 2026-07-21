# C# Security

C# security depends on dependency hygiene, secure framework configuration, input validation, and secret handling.

## High-Risk Patterns

- SQL string concatenation.
- Disabled TLS validation.
- Secrets in configuration files.
- Unsafe deserialization.
- Overly broad reflection.
- Insecure authorization checks.

TStack should mark credential exposure, unsafe deserialization, or missing authorization review as high risk.

# Java Security

Java security depends on dependency control, safe serialization, input validation, and framework configuration.

## High-Risk Patterns

- Unsafe deserialization.
- SQL string concatenation.
- XML processing without secure parser settings.
- Secrets in configuration files.
- Overly broad reflection.
- Disabled TLS or certificate validation.

## Required Controls

- Managed dependencies.
- Security review for authentication and authorization.
- Input validation at service boundaries.
- Secret redaction in logs.
- Vulnerability scanning where available.

TStack should mark unresolved credential exposure or unsafe deserialization evidence as `HOLD`.

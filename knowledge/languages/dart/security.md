# Dart Security

Dart security for apps depends on secret handling, platform storage, transport security, dependency review, and backend boundary validation.

## High-Risk Patterns

- Secrets in app bundles.
- Insecure local storage.
- Disabled TLS validation.
- Missing runtime validation for API data.
- Overbroad permissions.

TStack should mark exposed secrets, insecure storage, or unreviewed permissions as high risk.

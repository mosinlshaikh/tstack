# Swift Security

Swift security depends on platform permissions, secure storage, transport security, dependency review, and safe handling of user data.

## High-Risk Patterns

- Secrets in app bundles.
- Insecure local storage.
- Disabled certificate validation.
- Overbroad platform permissions.
- Unsafe handling of URLs, files, or intents.

TStack should mark exposed secrets, insecure storage, or missing signing/release evidence as high risk.

# Kotlin Security

Kotlin security follows JVM and Android security foundations plus coroutine and lifecycle discipline.

## High-Risk Patterns

- Secrets in app resources or repository files.
- Unsafe WebView or intent handling on Android.
- SQL string concatenation.
- Missing TLS validation.
- Unbounded coroutine launches.
- Insecure local storage.

TStack should mark hardcoded credentials, unsafe storage of secrets, or missing release signing evidence as high risk.

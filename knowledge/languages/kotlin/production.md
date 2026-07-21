# Kotlin Production

Production Kotlin requires target-version clarity, dependency control, runtime configuration, and platform-specific release evidence.

## Required Signals

- JVM or Android target declared.
- Gradle build is reproducible enough for release.
- Tests run in CI.
- Android signing and manifest risks are reviewed where applicable.
- Observability exists for services.

TStack should increase risk when release configuration, target SDK, or runtime configuration is undocumented.

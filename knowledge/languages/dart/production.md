# Dart Production

Production Dart and Flutter projects require SDK constraints, dependency control, build configuration, and platform release evidence.

## Required Signals

- SDK constraint declared.
- `pubspec.lock` committed for applications.
- Tests run in CI.
- Platform release process documented.
- Secrets and environment handling reviewed.

TStack should increase risk when release target, signing, or platform configuration is unclear.

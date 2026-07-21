# Dart Performance

Dart performance in Flutter depends on rendering, state updates, startup, memory, and platform-channel behavior.

## Guidance

- Measure on target devices.
- Avoid unnecessary rebuilds.
- Keep expensive work off UI-critical paths.
- Review asset size and startup time.
- Use profiling before optimization.

TStack should raise risk when UI-critical changes lack device testing or profiling evidence.

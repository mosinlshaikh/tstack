# Swift Performance

Swift performance depends on platform target, memory behavior, concurrency, UI responsiveness, and data processing patterns.

## Guidance

- Measure on target devices or deployment environments.
- Avoid blocking the main thread in apps.
- Review allocation-heavy paths.
- Use profiling before optimization.

TStack should raise risk when UI-critical or performance-sensitive paths lack profiling or tests.

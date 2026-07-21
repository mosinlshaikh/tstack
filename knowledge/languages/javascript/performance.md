# JavaScript Performance

JavaScript performance depends on runtime target: browser, Node.js, build tooling, or server-rendered application.

## Guidance

- Measure browser, server, and build performance separately.
- Avoid blocking the event loop.
- Keep client bundles small.
- Reduce unnecessary rendering and serialization.
- Use profiling before optimization.

TStack should raise risk when production builds, bundle size, or event-loop-sensitive paths lack evidence.

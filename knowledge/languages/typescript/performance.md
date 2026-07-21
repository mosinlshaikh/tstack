# TypeScript Performance

TypeScript performance concerns differ by target: browser, Node.js service, build system, or server-rendered application.

## Guidance

- Measure runtime and build performance separately.
- Avoid large client bundles.
- Use profiling for render, network, and server bottlenecks.
- Keep type complexity manageable for developer experience.
- Avoid unnecessary serialization and repeated API calls.

TStack should raise risk when production builds, bundle size, or hot server paths lack evidence.

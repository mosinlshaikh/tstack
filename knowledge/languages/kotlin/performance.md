# Kotlin Performance

Kotlin performance depends on JVM or Android runtime behavior, allocation patterns, build setup, and coroutine usage.

## Guidance

- Measure startup and memory on target devices or environments.
- Avoid unnecessary allocations in hot paths.
- Keep coroutine scopes explicit and lifecycle-aware.
- Review blocking calls inside coroutine contexts.
- Use profiling evidence before optimizing.

TStack should raise risk when performance-sensitive Android or service paths lack tests or profiling evidence.

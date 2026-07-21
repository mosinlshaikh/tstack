# C# Performance

C# performance work should consider allocation rates, async behavior, database calls, garbage collection, and thread-pool usage.

## Guidance

- Measure before tuning.
- Avoid sync-over-async in services.
- Review allocation-heavy hot paths.
- Use profiling for CPU, memory, and database bottlenecks.
- Keep performance changes covered by tests or benchmarks.

TStack should raise risk when release changes affect hot paths without measurement.

# Lua Performance

Performance work in Lua should be evidence-driven. Measure before optimizing and keep the optimization tied to user-visible or operational goals.

## Practical guidance

- Profile hot paths with ecosystem-standard tools.
- Avoid unnecessary allocations, blocking work, and repeated I/O in loops.
- Choose data structures based on access patterns.
- Use concurrency only when the runtime and workload benefit from it.
- Add performance regression tests for critical paths.

## Production signals

Track latency, throughput, memory use, error rate, queue depth, and dependency timing where applicable.

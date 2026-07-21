# Python Performance

Python performance work should start with measurement. Guessing often leads to unnecessary complexity.

## Performance Model

Common bottleneck types:

- CPU-bound loops and transformations.
- I/O-bound network or disk waits.
- Database query volume.
- Serialization and deserialization overhead.
- Startup time.
- Memory growth from large collections or retained references.

## Optimization Strategy

Recommended order:

1. Define the performance target.
2. Measure with representative data.
3. Identify the bottleneck.
4. Optimize the smallest responsible unit.
5. Verify behavior and performance after the change.

## Practical Techniques

Useful approaches:

- Use efficient data structures.
- Batch external calls.
- Avoid repeated expensive work in loops.
- Push filtering and aggregation into the database when appropriate.
- Use async I/O for high-concurrency I/O-bound services.
- Use multiprocessing, native extensions, vectorized libraries, or another service for CPU-bound hotspots.
- Cache only when invalidation and memory cost are understood.

## Anti-Patterns

Avoid:

- Optimizing without a baseline.
- Replacing simple code with complex concurrency before proving need.
- Hiding slow database access behind helper functions without visibility.
- Adding caches without expiration or invalidation strategy.
- Treating async as a universal performance fix.

## TStack Performance Signals

TStack should raise review priority when it finds:

- Very large source files.
- Missing tests around performance-sensitive modules.
- No clear runtime constraints.
- High-impact graph nodes with no focused test coverage.
- Release changes without benchmark evidence for known performance-critical systems.

# Go Performance

Go is often fast enough by default, but production performance still requires measurement.

## Common Bottlenecks

- Excessive allocations.
- Lock contention.
- Goroutine leaks.
- Channel misuse.
- Inefficient serialization.
- Database or network round trips.

## Optimization Strategy

Recommended order:

1. Define service-level targets.
2. Benchmark or profile representative workloads.
3. Inspect allocations, CPU, blocking, and goroutine behavior.
4. Optimize the smallest responsible path.
5. Re-test correctness and performance.

## Practical Techniques

- Use `context.Context` consistently for cancellation.
- Avoid unbounded goroutine creation.
- Use worker pools only when they match the workload.
- Prefer simple data structures before clever abstractions.
- Use profiling tools before rewriting code.

## TStack Performance Signals

TStack should raise risk when:

- Concurrency-heavy code has weak tests.
- Critical services lack benchmarks.
- High-impact modules have no race test plan.
- Release changes affect hot paths without evidence.

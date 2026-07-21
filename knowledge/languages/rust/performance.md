# Rust Performance

Rust gives strong control over performance, but measurement remains required.

## Common Bottlenecks

- Unnecessary allocations.
- Excessive cloning.
- Lock contention.
- Inefficient serialization.
- Poor async task boundaries.
- Suboptimal data layout.

## Optimization Strategy

Recommended order:

1. Define performance targets.
2. Benchmark representative workloads.
3. Profile CPU, memory, and lock behavior.
4. Reduce allocations or contention where evidence points.
5. Preserve safety and tests while optimizing.

## Practical Techniques

- Prefer clear ownership before micro-optimizing.
- Avoid clones in hot paths unless they are measured as acceptable.
- Use iterators and slices where appropriate.
- Be explicit about async runtime boundaries.
- Keep unsafe optimization isolated and justified.

## TStack Performance Signals

TStack should raise risk when:

- Performance-critical modules lack benchmarks.
- Unsafe optimizations lack tests.
- High-impact graph nodes have weak coverage.
- Release notes claim performance changes without evidence.

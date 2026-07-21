# C Performance

C provides strong performance control, but correctness and safety come first.

## Guidance

- Measure with representative workloads.
- Preserve defined behavior.
- Avoid unsafe micro-optimizations without evidence.
- Review cache behavior, allocation strategy, and data layout.
- Use profiling and benchmarks before rewriting.

TStack should raise risk when performance changes weaken safety checks or lack benchmark evidence.

# Assembly Performance

Performance work in Assembly should start with measurement. TStack does not approve speculative optimization as a substitute for profiling.

## Practical guidance

- Profile representative workloads before changing architecture.
- Track memory, CPU, I/O, startup time, and latency where relevant.
- Choose data structures and concurrency patterns based on measured access patterns.
- Avoid repeated expensive work inside loops or request paths.
- Add regression checks for performance-sensitive code.

## Risk boundary

Optimization must not reduce correctness, security, observability, or rollback ability.

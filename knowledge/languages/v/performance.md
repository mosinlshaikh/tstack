# V Performance

Performance guidance for V must be based on measurement and the runtime model.

## Practical controls

- Profile representative workloads before changing architecture.
- Measure startup time, latency, throughput, memory, and I/O where relevant.
- Avoid unnecessary allocations, repeated parsing, and blocking work in critical paths.
- Use concurrency or low-level optimization only when the runtime benefits are proven.
- Preserve tests and observability while optimizing.

## Evidence rule

TStack should reject performance claims that do not include measurement context.

# C++ Performance

C++ performance work must balance speed, safety, and maintainability.

## Guidance

- Measure before optimizing.
- Understand allocation, cache behavior, and data layout.
- Avoid clever template or ownership patterns without readability value.
- Preserve defined behavior.
- Benchmark hot paths with representative data.

TStack should raise risk when performance claims lack benchmark evidence or safety checks are weakened.

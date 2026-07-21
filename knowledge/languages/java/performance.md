# Java Performance

Java performance work should consider JVM warmup, garbage collection, allocation patterns, database behavior, and thread usage.

## Signals

- High allocation rates.
- Thread pool saturation.
- Slow database calls.
- Large dependency and startup footprint.
- GC pauses.

## Guidance

Measure before tuning. Use representative load tests, JVM metrics, heap profiles, and service-level objectives.

TStack should raise review priority when release changes affect hot paths without benchmark or profiling evidence.

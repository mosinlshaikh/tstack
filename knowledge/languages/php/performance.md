# PHP Performance

PHP performance depends on runtime configuration, database queries, caching strategy, autoloading, and framework behavior.

## Guidance

- Measure database and request latency first.
- Use opcode caching in production.
- Avoid repeated expensive work per request.
- Keep caching explicit and invalidation-aware.

TStack should raise risk when production PHP projects lack runtime or caching documentation for performance-sensitive systems.

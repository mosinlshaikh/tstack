# Benchmarks

TStack benchmarks must be machine-readable and must not fabricate scale claims.

Current benchmark:

```bash
tstack benchmark kernel --tasks 100 --workers 4 --output benchmark.json
```

This creates approved queued filesystem tasks in a local SQLite workspace, runs them through the same-process worker foundation, and reports:

- logical task count
- requested workers
- duration
- attempted tasks
- succeeded
- failed
- throughput
- audit-chain validity
- limitations

## Limitations

The current benchmark is same-process and local. It does not prove distributed execution, a background daemon, or 1000-agent support.

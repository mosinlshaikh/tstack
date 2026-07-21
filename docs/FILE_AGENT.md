# File Manager Agent

The File Manager Agent is the first practical local desktop capability.

Current behavior:

- Scans local directories.
- Builds a file inventory.
- Counts extensions.
- Detects duplicate files by SHA-256 content hash.
- Produces Markdown or JSON reports.
- Does not delete, move, rename, or modify files.

## Command

```bash
tstack file inventory .
tstack file inventory C:\Users\Example\Downloads --format json
```

## Safety Boundary

Execution is disabled. Duplicate detection is report-only. Future organize, move, rename, archive, and trash actions must use approval, audit, backup, and rollback controls.

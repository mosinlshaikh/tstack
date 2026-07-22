# Secure Execution Journal

Status: experimental.

TStack records durable JSONL events around signed secure actions.

Each event contains:

- execution ID
- request ID
- capability
- lifecycle state
- result digest when available
- previous-entry hash
- current-entry hash
- UTC timestamp

Supported lifecycle states currently include `started`, `completed`, and `failed`.

`execute_with_journal()` fsyncs the `started` event before invoking an operation and appends either a `completed` event with a SHA-256 receipt digest or a `failed` event before re-raising the error.

`verify_execution_journal()` detects edited, deleted, reordered, or malformed entries.

## Boundary

The journal is tamper-evident but is not yet externally anchored or digitally signed. File-plan crash recovery still requires a per-move persistent recovery journal.

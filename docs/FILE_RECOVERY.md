# File Transaction Recovery

Status: **experimental recovery foundation**

TStack now provides a durable, hash-chained recovery journal for file move transactions.

## State model

```text
PREPARED
→ MOVED (one event per completed move)
→ VERIFIED
→ COMMITTED
```

If a process stops before a terminal state, recovery tooling can reverse recorded `MOVED` operations in reverse order and append:

```text
RESTORED
→ ROLLED_BACK
```

## Guarantees

- Each journal append is flushed and `fsync`-ed.
- Every event is linked to the previous event hash.
- Sequence, transaction identity, and event digests are verified before recovery.
- Recovery refuses invalid or tampered journals.
- Paths are resolved inside an explicitly supplied transaction root.
- Terminal transactions are not replayed.

## Current boundary

The recovery engine is implemented and tested as a standalone primitive. The secure file executor must still emit `PREPARED`, per-move `MOVED`, `VERIFIED`, and `COMMITTED` events directly during execution before crash recovery is considered end-to-end complete.

The legacy unsigned `tstack sandbox run` path also remains present pending a compatibility-safe CLI migration. Use `tstack-secure` for signed execution.

# Audit Log

TStack audit logs are append-only JSONL hash chains for runtime audit events.

```bash
tstack runtime audit request.json --decision decision.json --outcome approved --format json --output event.json
tstack audit-log append .tstack/audit.jsonl event.json
tstack audit-log verify .tstack/audit.jsonl
```

Every entry stores:

- event payload
- previous entry hash
- current entry hash
- sequential index

If an old entry is edited, removed, reordered, or corrupted, verification fails.

This is not a digital signature. It is tamper-evident local history. Publisher or approver identity should later be strengthened with signed approvals.

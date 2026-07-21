# Capability Model

TStack public capabilities must be labeled honestly:

- `WORKING`
- `EXPERIMENTAL`
- `PLAN-ONLY`
- `UNSUPPORTED`

```bash
tstack capability list
tstack capability list --status EXPERIMENTAL --format json
tstack capability show filesystem.write
tstack capability validate
```

Each capability definition includes:

- status
- risk
- required permission
- approval requirement
- input/output contract summary
- timeout
- rollback support
- audit behavior
- platform support

The registry prevents blueprint capabilities from being described as working runtime integrations.

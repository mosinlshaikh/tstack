# Controlled Executor

The executor is the bridge after approval. Its foundation is intentionally narrow.

Current behavior:

- Creates dry-run execution plans.
- Allows only approved low-risk documentation-like actions to become executable plans.
- Can apply a narrow append-only documentation update when `--apply` and `--target` are explicit.
- Blocks high-risk, production, SSH, secret, auth, payment, and deployment actions.

## Commands

```bash
tstack execute plan approval.json decision.json
tstack execute plan approval.json decision.json --format json
tstack execute plan approval.json decision.json --target README.md --apply
```

## Exit Code

- `0`: execution plan is eligible as a dry-run plan.
- `15`: execution plan is blocked by approval, risk, or executor policy.

## Boundary

Apply mode is limited to approved low-risk documentation-like actions on existing `.md` or `.txt` files. It creates a backup and performs an append-only update. Future broader execution requires tests, policy checks, rollback verification, and explicit approval enforcement.

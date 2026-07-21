# Controlled Executor

The executor is the bridge after approval. Its foundation is intentionally narrow.

Current behavior:

- Creates dry-run execution plans.
- Allows only approved low-risk documentation-like actions to become executable plans.
- Keeps actual execution disabled.
- Blocks high-risk, production, SSH, secret, auth, payment, and deployment actions.

## Commands

```bash
tstack execute plan approval.json decision.json
tstack execute plan approval.json decision.json --format json
```

## Exit Code

- `0`: execution plan is eligible as a dry-run plan.
- `15`: execution plan is blocked by approval, risk, or executor policy.

## Boundary

Even when a plan is eligible, `execution_allowed` remains `false`. Future execution requires a separate implementation with tests, policy checks, rollback verification, and explicit approval enforcement.

# Approval Engine

The Approval Engine is the safety gate between agentic planning and future execution.

It can:

- Create approval requests.
- Classify action risk.
- Record human approval or rejection.
- Preserve execution as blocked until a future executor performs additional checks.

## Commands

Create a request:

```bash
tstack approval request "Deploy to production over SSH"
```

JSON request file:

```bash
tstack approval request "Update README" --format json --output approval.json
```

Record a decision:

```bash
tstack approval decide approval.json --approved --approver Mosin --reason "Reviewed and accepted."
```

Evaluate readiness:

```bash
tstack approval readiness approval.json decision.json
```

## Boundary

Approval records intent. It does not execute the action.

Execution remains disabled until a future executor verifies:

- Policy.
- Risk level.
- Tests.
- Security checks.
- Rollback readiness.
- Human approval.

Readiness currently remains blocked because the execution module is not implemented yet.

# Bug Finder

The Bug Finder creates a safe diagnostic report from repository scan findings and optional failure text.

It can:

- Inspect existing TStack scan findings.
- Accept failure text from tests, CI, security, performance, or UI checks.
- Route the issue to the responsible agent.
- Propose a fix plan.
- Provide verification steps.

It does not edit code automatically.

## Command

```bash
tstack bug find .
tstack bug find . --failure "pytest failed assertion in test_app"
tstack bug find . --failure "GitHub Actions build failed" --format json
```

## Exit Code

- `0`: no bug findings detected.
- `16`: review or hold bug findings exist.

## Boundary

Bug solving is currently plan-only. Future code fixes must go through approval, executor policy, tests, and rollback checks.

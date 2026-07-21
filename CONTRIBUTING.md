# Contributing to TStack

## Workflow

1. Open or select an issue describing the problem and acceptance criteria.
2. Create a focused branch from `main`.
3. Make the smallest safe change that satisfies the requirement.
4. Add or update tests and documentation.
5. Run the relevant review, QA, security and release checks.
6. Open a pull request with evidence, risks and rollback notes.

## Pull Request Requirements

Every pull request should include:

- problem statement and scope
- implementation summary
- validation evidence
- security and data-impact assessment
- known limitations
- rollback approach

## Engineering Rules

- Never commit secrets, credentials or production data.
- Never fabricate test results or operational evidence.
- Preserve backward compatibility unless a breaking change is approved.
- Prefer explicit failure over silent corruption.
- Keep generated files and unrelated formatting changes out of focused patches.

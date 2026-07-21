# TStack Ship

## Objective
Release a known, traceable artifact safely with validation, observability and rollback.

## Procedure
1. Confirm immutable artifact identity, version and approved scope.
2. Verify tests, security checks, configuration, migrations and backups.
3. Define staged deployment, health signals and abort thresholds.
4. Execute post-release verification and record outcome.

## Guardrails
- No rollback plan means no release.
- Unknown artifact or configuration means HOLD.
- Unresolved critical defects block release.
- Never claim success without production verification.

## Output
Provide release decision, artifact identity, checklist, deployment steps, health checks, rollback plan and post-release evidence.

# /ship

Prepare and authorize a controlled release only after engineering gates are satisfied.

## Required evidence
- Approved scope and acceptance criteria
- Review decision with no unresolved release blocker
- QA results and disclosed skipped tests
- Security review appropriate to the change
- Build or package artifact identification
- Deployment and rollback procedure

## Procedure
1. Confirm the exact commit, version, environment, and artifact.
2. Summarize user-visible and operational changes.
3. Verify configuration, migrations, backups, and secrets.
4. Check monitoring, alerts, logs, and ownership.
5. Define staged rollout and measurable success signals.
6. Define rollback trigger and tested recovery steps.
7. Produce release notes and final go/no-go decision.

## Automatic no-go conditions
- Unknown artifact or commit
- Destructive migration without verified backup and rollback
- Unresolved critical/high defect
- Missing production credentials or configuration
- No observable success/failure signal
- No accountable release owner

## Output
- Go/no-go decision
- Release checklist
- Deployment sequence
- Verification and monitoring plan
- Rollback plan
- Release notes

# TStack Decision Brain

The Decision Brain converts current TStack scan evidence and local learning memory into an explainable, ranked remediation plan.

## Generate a plan

```bash
tstack scan . --format json --output .tstack/latest-scan.json --fail-on never
tstack-decide .tstack/latest-scan.json \
  --memory .tstack/learning-memory.json \
  --output .tstack/decision-plan.md
```

Machine-readable output:

```bash
tstack-decide .tstack/latest-scan.json \
  --format json \
  --output .tstack/decision-plan.json
```

## Inputs

- Current scan findings and project fingerprint
- Local learning history
- Finding severity
- Recurrence and explicit human feedback
- Scanner remediation guidance

## Outputs

Each ranked action includes:

- Rule and affected path
- Severity, confidence, and priority
- Evidence-backed rationale
- Proposed remediation
- Post-change verification instruction
- Explicit approval requirement

## Safety boundary

The Decision Brain is advisory. It cannot:

- Modify source code or configuration
- Execute shell or SSH commands
- Access credentials
- Change policies
- Deploy or release software
- Approve its own recommendations

Every action has `approval_required=true` and `execution_allowed=false`. A human must review the evidence, authorize a change, execute it through an appropriate controlled workflow, and rerun verification.

## Exit codes

- `0` — no remediation actions; PASS
- `1` — invalid input or operational failure
- `11` — plan contains REVIEW or HOLD actions

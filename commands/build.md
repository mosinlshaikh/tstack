# /build

Implement an approved plan with minimal, reviewable changes.

## Inputs
- Approved architecture or issue
- Target repository and branch
- Acceptance criteria
- Constraints and non-goals

## Procedure
1. Reconfirm scope and affected components.
2. Inspect existing conventions before writing code.
3. Break work into the smallest safe patches.
4. Preserve backward compatibility unless explicitly approved otherwise.
5. Add or update tests with each behavior change.
6. Run relevant static checks, tests, and build commands.
7. Record assumptions, evidence, and unresolved risks.

## Guardrails
- Never invent APIs, files, configuration, or test results.
- Never overwrite production data or secrets.
- Do not perform broad refactors during a targeted fix.
- Stop when critical requirements conflict.
- No successful verification = no completion claim.

## Output
- Files changed and why
- Verification commands and results
- Known limitations
- Rollback instructions
- Recommended next command: `/review`

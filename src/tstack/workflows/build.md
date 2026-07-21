# TStack Build

## Objective
Implement the smallest production-safe change that satisfies verified acceptance criteria.

## Procedure
1. Confirm scope, interfaces, invariants and affected data.
2. Create an implementation slice with explicit failure handling.
3. Add tests, logging and migration or rollback steps where relevant.
4. Validate behavior against acceptance criteria.

## Guardrails
- Preserve existing user data and public contracts.
- Avoid unrelated refactors.
- Never hide failed validation.
- Every risky change must be reversible.

## Output
Provide changed components, implementation notes, tests, evidence, known limitations and rollback instructions.

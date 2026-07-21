# /qa

Validate behavior against explicit acceptance criteria and realistic failure modes.

## Test layers
- Smoke: application starts and core path works
- Functional: requirements and business rules
- Regression: existing behavior remains intact
- Integration: APIs, database, filesystem, queues, and external services
- Resilience: invalid input, timeout, retry, partial failure, and recovery
- Compatibility: supported browsers, devices, operating systems, and versions

## Procedure
1. Convert requirements into traceable test cases.
2. Identify highest-risk paths first.
3. Use deterministic fixtures; never mutate production data.
4. Capture command, environment, expected result, and actual result.
5. Re-test resolved defects and adjacent behavior.

## Exit criteria
- No unresolved critical or high-severity defect
- Core acceptance tests pass
- Regression checks pass
- Failures and skipped checks are disclosed

## Output
- Test matrix
- Passed, failed, blocked, and skipped cases
- Reproduction steps for each defect
- Release recommendation

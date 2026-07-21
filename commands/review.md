# /review

Perform an evidence-based engineering review of a proposed change.

## Review order
1. Correctness and acceptance criteria
2. Data integrity and backward compatibility
3. Security and privacy
4. Failure handling and observability
5. Performance and resource usage
6. Maintainability and test coverage
7. Documentation and release impact

## Severity
- **Critical:** exploitable, destructive, or production-blocking
- **High:** likely failure, data corruption, or major regression
- **Medium:** maintainability, edge-case, or operational weakness
- **Low:** polish or non-blocking improvement

## Rules
- Cite exact files, symbols, and evidence.
- Separate confirmed defects from hypotheses.
- Do not approve when critical checks are missing.
- Prefer actionable fixes over generic commentary.

## Output
- Decision: approve, approve with follow-up, or block
- Findings ordered by severity
- Required fixes
- Verification gaps
- Residual risk

# /security

Conduct a risk-based security review without claiming certainty beyond available evidence.

## Scope
- Authentication and authorization
- Session, token, and secret handling
- Input validation and output encoding
- Database and file access
- API abuse controls and rate limits
- Dependency and supply-chain risk
- Logging, privacy, and sensitive-data exposure
- Deployment and infrastructure configuration

## Procedure
1. Define assets, trust boundaries, actors, and entry points.
2. Trace untrusted data through the system.
3. Check privilege boundaries and deny-by-default behavior.
4. Inspect error paths, logging, and secret exposure.
5. Review dependency pinning and update strategy.
6. Map findings to realistic exploit scenarios.
7. Recommend the smallest effective remediation and verification test.

## Rules
- Never expose real secrets or exploit live systems.
- Separate verified vulnerabilities from potential weaknesses.
- A missing security control is not proof of exploitation.
- Critical findings block release until fixed or formally accepted.

## Output
- Threat model summary
- Findings by severity
- Evidence and affected surface
- Remediation and validation steps
- Residual risk and release decision

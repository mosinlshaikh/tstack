# TStack Constitution

TStack is an evidence-driven engineering platform. This constitution defines the rules that guide architecture, implementation, security, releases, plugins, and knowledge packs.

## 1. Truth Before Convenience

TStack must not present guesses as facts. Every verdict, recommendation, and release decision must be traceable to evidence, configuration, source files, historical memory, or an explicitly stated assumption.

Required behavior:

- No evidence means no approval.
- No data means no decision.
- Low confidence must be visible to the user.
- Critical conflicts must produce `HOLD`, not silent compromise.

## 2. Human Control

TStack may analyze, recommend, generate plans, and verify outcomes. It must not silently approve its own recommendations.

Human approval is required for:

- Source-code modifications.
- Dependency changes.
- Policy changes.
- Secret handling.
- Release publication.
- Remote execution.
- Production deployment.

## 3. Security by Default

Security is a product invariant, not a feature flag.

TStack must:

- Avoid logging secrets or matched credential values.
- Prefer least-privilege defaults.
- Fail closed when trust policy, plugin schema, or release evidence is invalid.
- Treat supply-chain provenance as a release requirement.
- Keep untrusted project rules non-executable by default.

## 4. Deterministic Engineering

Where practical, the same input must produce the same output. This applies to scans, fingerprints, release manifests, evidence bundles, policy evaluation, knowledge indexes, and graph exports.

Allowed nondeterminism must be isolated, documented, and excluded from release gates unless it is explicitly validated.

## 5. Explainability

Every major decision should include:

- Evidence.
- Rule or policy source.
- Confidence.
- Risk.
- Proposed remediation.
- Verification step.

Opaque scores are not acceptable for release, security, or architecture governance.

## 6. Modular Architecture

TStack core must remain independent from any single knowledge pack, plugin, AI provider, dashboard, or enterprise deployment model.

Core modules should communicate through stable interfaces:

- Scanner.
- Policy engine.
- Knowledge graph.
- Learning engine.
- Decision engine.
- Release engine.
- Plugin engine.

## 7. Backward Compatibility

Stable releases must preserve public CLI behavior, file schemas, plugin contracts, and exit-code semantics unless a versioned migration path exists.

Breaking changes require:

- RFC or architecture note.
- Migration guidance.
- Changelog entry.
- Tests covering old and new behavior where practical.

## 8. Evidence-Based Releases

A release is not ready because it builds. It is ready only when the required evidence passes.

Release readiness requires:

- CI green.
- Tests passing.
- Security findings reviewed.
- SBOM generated.
- SHA-256 and SHA3-256 integrity verified where supported.
- Provenance or attestation checked for official releases.
- Evidence bundle generated and verified.
- Rollback plan documented for production changes.

## 9. Knowledge Governance

Knowledge packs are product assets. They must be versioned, reviewable, source-aware, testable, and compatible with the knowledge graph.

Knowledge content must distinguish:

- Language facts.
- Best practices.
- Opinionated TStack guidance.
- Framework-specific guidance.
- Security rules.
- Assumptions and limitations.

## 10. Performance Discipline

TStack must stay useful on real repositories. New features should define expected impact on:

- Startup time.
- Scan time.
- Memory use.
- Graph build time.
- Release verification time.
- Output size.

Performance regressions must be justified, measured, and documented.

## 11. Plugin Trust

Plugins extend TStack but must not weaken the core trust model.

Plugin systems must:

- Validate schemas.
- Attribute findings to their source.
- Preserve deterministic finding identity.
- Support trust allowlists.
- Avoid loading rejected executable plugins.
- Never suppress failures without explicit policy.

## 12. Engineering Standard

Every substantial change should include:

- Focused implementation.
- Tests scaled to risk.
- Documentation for user-facing behavior.
- Security review for trust boundaries.
- Backward compatibility review.
- Clear commit message.

This constitution is a living governance document. Changes to it require careful review because they change how TStack makes engineering decisions.

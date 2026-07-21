# TStack Architecture

TStack is designed as a modular engineering intelligence platform. The core must stay deterministic, testable, and independent from any single plugin, knowledge pack, dashboard, or AI provider.

## Architecture Principles

- Evidence first: decisions come from files, policies, scans, manifests, memory, and verified reports.
- Human approval: TStack recommends and verifies; it does not silently approve risky actions.
- Modular core: engines communicate through stable contracts.
- Versioned data: reports, manifests, policies, baselines, and knowledge indexes use explicit schemas.
- Secure defaults: untrusted code is not executed by default, and secrets are not exposed in reports.

## Layer Model

```text
User Interfaces
    |
CLI Commands, Reports, Future Dashboard
    |
Engineering Engines
    |
Knowledge, Policy, Graph, Memory, Release Evidence
    |
Project Repository and Artifacts
```

## Core Engines

### Scanner Engine

Discovers project files, detects frameworks, evaluates engineering controls, and emits deterministic findings.

Responsibilities:

- File inventory.
- Framework detection.
- Security and quality checks.
- Risk scoring.
- Markdown, JSON, and SARIF outputs.

### Policy Engine

Applies project policy to scanner findings.

Responsibilities:

- Threshold enforcement.
- Allowlist handling.
- Baseline comparison.
- Exit-code decisions.
- Audit visibility for suppressed findings.

### Remediation Engine

Generates safe missing controls.

Responsibilities:

- Dry-run by default.
- No application-code modifications.
- No dependency or lockfile changes.
- No credential handling.
- Idempotent file creation.

### Plugin Engine

Extends scanning through declarative rules and installed rule plugins.

Responsibilities:

- Project rule validation.
- Plugin attribution.
- Integrity metadata.
- Trust allowlist enforcement.
- Fail-closed behavior for invalid plugins.

### Release Engine

Builds and verifies release evidence.

Responsibilities:

- SBOM generation.
- Artifact manifests.
- SHA-256 and SHA3-256 verification.
- Reproducible-build comparison.
- Attestation receipt validation.
- Trust-gate decisions.

### Evidence Bundle Engine

Creates tamper-evident bundles for release reports and verification artifacts.

Responsibilities:

- Evidence file inventory.
- Dual-hash records.
- Deterministic Merkle root.
- Verification report.

### Learning Engine

Stores local feedback about recurring findings.

Responsibilities:

- Finding recurrence tracking.
- Human feedback capture.
- Recommendation ranking.
- Local memory persistence.

### Decision Engine

Combines current scan evidence with learning memory to produce prioritized remediation plans.

Responsibilities:

- Action ranking.
- Confidence reporting.
- Approval-required boundaries.
- Verification guidance.

### Knowledge Graph Engine

Builds a project relationship graph.

Responsibilities:

- File nodes.
- Test-to-source relationships.
- Static import relationships.
- Impact analysis.
- DOT export.
- Deterministic graph fingerprint.

## Knowledge Layer

Knowledge packs are separate from the core engine. They provide curated engineering guidance for languages, frameworks, architecture, security, testing, DevOps, AI, and databases.

Knowledge packs must be:

- Versioned.
- Indexed.
- Reviewable.
- Source-aware where applicable.
- Graph-compatible.
- Clearly separated from internal model knowledge.

## Data Contracts

TStack treats the following as public or semi-public contracts:

- CLI commands and flags.
- Exit codes.
- Scan JSON.
- Policy JSON.
- Baseline JSON.
- SARIF output.
- Release manifests.
- Evidence bundle JSON.
- Knowledge index JSON.
- Plugin rule schema.

Contract changes require versioning and migration guidance.

## Trust Boundaries

High-risk boundaries:

- Project-provided rules.
- Installed Python plugins.
- Release artifacts.
- Attestation receipts.
- Baseline and allowlist policy.
- Knowledge packs from third parties.

TStack must validate these boundaries before trusting their contents.

## Future Architecture

The planned platform expands into:

- Semantic Context Engine.
- Language Brain.
- Multi-Agent Orchestrator.
- Engineering Memory OS.
- Engineering Dashboard.
- Enterprise policy and audit layer.

These additions must plug into the existing evidence-first architecture rather than replacing it with opaque automation.

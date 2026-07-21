# TStack Roadmap

This roadmap keeps TStack focused on stable, evidence-driven engineering rather than feature accumulation.

## Current Position

TStack is an alpha engineering CLI with repository scanning, policy gates, safe remediation, plugin rules, supply-chain verification, learning memory, decision planning, and a knowledge graph.

The next priority is to stabilize these foundations before expanding into larger intelligence and enterprise features.

## Phase 1: v1.0 Beta Foundation

Goal: make TStack reliable enough for early external users and contributors.

Required outcomes:

- CI is consistently green.
- Public CLI commands are documented.
- Exit codes are stable.
- Core schemas are versioned.
- Plugin SDK behavior is documented.
- Knowledge graph behavior is documented.
- Decision and learning engines remain approval-based.
- Release trust flow is documented and testable.
- Foundation documents are present.

Primary deliverables:

- `CONSTITUTION.md`.
- `ROADMAP.md`.
- `ARCHITECTURE.md`.
- `VERSIONING.md`.
- RFC process.
- Knowledge framework.
- Stable v1.0 beta checklist.

## Phase 2: Engineering Knowledge Base

Goal: add maintainable, versioned engineering knowledge without bloating the core engine.

Planned capabilities:

- Knowledge pack format.
- Knowledge index.
- Language and framework maps.
- Searchable topic metadata.
- Knowledge graph integration.
- First language packs.
- Security and architecture guidance packs.

Initial knowledge packs:

- Python.
- Go.
- Rust.
- Java and Kotlin.
- JavaScript and TypeScript.
- SQL and databases.
- DevOps foundations.

## Phase 3: Language Brain

Goal: provide explainable language and architecture recommendations.

Planned capabilities:

- Compare language suitability for a project.
- Explain runtime, security, testing, and deployment tradeoffs.
- Recommend stack choices from evidence and constraints.
- Link recommendations to knowledge pack topics.

The Language Brain must not claim to contain model internals. It uses curated knowledge, rules, project evidence, and documented assumptions.

## Phase 4: Multi-Agent Foundation

Goal: allow specialized engineering agents to produce evidence-backed assessments under an orchestrator.

Planned agents:

- Architect.
- Security.
- QA.
- Performance.
- Documentation.
- Knowledge.
- Release.

The orchestrator resolves conflicts, reports uncertainty, and keeps human approval as the final control.

## Phase 5: Engineering Memory OS

Goal: make project history useful for future decisions.

Planned memory types:

- Project memory.
- Decision memory.
- Failure memory.
- Release memory.
- Policy memory.

Memory must be local-first, exportable, reviewable, and safe to delete.

## Phase 6: Enterprise Platform

Goal: support team usage and governance workflows.

Planned capabilities:

- Workspaces.
- RBAC.
- Audit logs.
- Policy management.
- Review queues.
- Compliance reports.
- Enterprise dashboard.

## Long-Term Vision

TStack should become an AI-assisted engineering operating system focused on:

- Architecture intelligence.
- Security governance.
- QA and release assurance.
- Knowledge management.
- Explainable engineering decisions.
- Human-approved automation.

The product must stay grounded in evidence, deterministic outputs, and maintainable architecture.

# TStack Architecture

## Operating Model

TStack is a modular workflow layer rather than a monolithic application. Each command accepts project context, applies explicit gates and produces an auditable output.

## Lifecycle

1. **Discover** — clarify the business goal, users, constraints and evidence.
2. **Architect** — define boundaries, components, data ownership, interfaces and risks.
3. **Build** — implement in small, reviewable increments.
4. **Review** — inspect correctness, maintainability, performance and regressions.
5. **Validate** — execute QA, security, data-integrity and acceptance checks.
6. **Ship** — version, deploy, verify and retain a rollback path.
7. **Operate** — monitor, learn and feed evidence into the next cycle.

## Command Contract

Every command should define:

- objective
- required inputs
- non-negotiable constraints
- execution procedure
- evidence requirements
- output format
- stop/hold conditions

## Global Gates

- **No evidence = no approval**
- **No data = no decision**
- **Conflicting critical evidence = hold**
- **Unbounded destructive action = reject**
- **Production change without rollback = reject**

## Planned Components

```text
commands/
  architect.md
  build.md
  review.md
  qa.md
  security.md
  design.md
  ship.md
  business.md
  ai-lab.md
  trading-lab.md

templates/
  project-brief.md
  architecture-decision-record.md
  pull-request.md
  release-checklist.md
```

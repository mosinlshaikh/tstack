# Agentic Engineering OS

TStack's agentic direction is to handle the complete software delivery lifecycle with explicit approval gates:

```text
Discovery -> Research -> Architecture -> UI/UX -> Build Plan -> QA -> Security -> Release -> Deployment Plan
```

The current implementation is intentionally **plan-only**. It creates structured agentic delivery plans but does not scrape private sources, edit files, run SSH, deploy software, or mutate production systems.

## Command

```bash
tstack agent plan "Build a hospital management system"
```

JSON output:

```bash
tstack agent plan "Build a SaaS CRM" --format json
```

Optional phase control:

```bash
tstack agent plan "Build API backend" --no-uiux --no-deployment
```

## Agent Phases

- Discovery and Research
- Architecture Planning
- Advanced UI/UX Design
- Implementation Plan
- Quality, Security, and Performance
- Release Readiness
- Deployment Plan

## Safety Model

- Every phase requires approval.
- Autonomous execution is disabled.
- Private or authenticated scraping requires explicit authorization.
- Deployment is planned, not executed.
- SSH remains plan-only.
- UI/UX work must include real flows, states, accessibility, and responsive behavior.

This gives TStack a safe foundation for powerful agentic workflows without silently crossing operational boundaries.

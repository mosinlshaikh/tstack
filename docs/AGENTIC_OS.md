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

List specialized agents:

```bash
tstack agent catalog
tstack agent catalog --category engineering
tstack agent show ui-ux-agent
tstack agent select "Medical Store Management System website with admin panel and deployment"
tstack agent orchestrate "Medical Store Management System website with admin panel and deployment"
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

## Agent Catalog

TStack includes 50+ specialized agent definitions across:

- Engineering
- Business
- Data and AI
- Design
- Operations
- Governance
- Orchestration

Every agent definition includes role, category, responsibilities, permissions, and approval boundaries.

## Agent Selection

The orchestrator can select relevant agents from a goal. For example, a website goal can select website builder, UI/UX, frontend, backend, database, SEO, security, QA, release, and deployment agents.

Selection is still plan-only and approval-gated.

## Orchestration

Agent orchestration maps selected agents into delivery phases:

- Discovery and Requirements
- Architecture and Data
- Advanced UI/UX
- Business and AI Features
- Implementation and Verification
- Release and Deployment
- Governance and Approval

This is the first step toward multi-agent collaboration while preserving explicit approval boundaries.

## Safety Model

- Every phase requires approval.
- Autonomous execution is disabled.
- Private or authenticated scraping requires explicit authorization.
- Deployment is planned, not executed.
- SSH remains plan-only.
- UI/UX work must include real flows, states, accessibility, and responsive behavior.

This gives TStack a safe foundation for powerful agentic workflows without silently crossing operational boundaries.

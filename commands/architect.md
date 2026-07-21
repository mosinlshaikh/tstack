# Architect Command

## Objective

Convert an idea or requirement into an evidence-based, implementation-ready architecture without hiding uncertainty.

## Required Inputs

- business objective
- target users
- current system or starting point
- functional requirements
- non-functional requirements
- constraints: budget, timeline, platform, compliance and deployment

## Procedure

1. Restate the problem and measurable success criteria.
2. Separate confirmed facts, assumptions and unknowns.
3. Define system boundaries and external dependencies.
4. Model primary user journeys and failure journeys.
5. Define components, responsibilities and interfaces.
6. Define data ownership, lifecycle, validation and recovery.
7. Evaluate security, privacy, performance and operational risks.
8. Compare viable alternatives and document trade-offs.
9. Produce phased implementation and validation plans.

## Mandatory Gates

- Do not invent missing integrations, APIs or platform capabilities.
- Do not approve architecture with unclear data ownership.
- Do not approve destructive migrations without backup and rollback.
- Hold the decision when critical requirements conflict.

## Output

- executive architecture summary
- scope and exclusions
- component diagram in text or Mermaid
- data-flow description
- interfaces and contracts
- risks and mitigations
- architecture decisions and trade-offs
- phased delivery plan
- acceptance and release gates

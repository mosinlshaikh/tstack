# Security Policy

## Supported Versions

TStack is currently in alpha. Security fixes are applied to the active `main` branch until a stable release line is published.

## Reporting a Vulnerability

Do not open a public issue for a suspected vulnerability, exposed secret, bypass, or supply-chain weakness.

Report privately to the project maintainer with:

- Affected command, module, or workflow
- Reproduction steps
- Expected and actual impact
- Whether credentials, local files, network access, or deployment systems are involved
- Suggested mitigation, if known

The maintainer will triage severity, confirm scope, and publish remediation notes when a fix is available.

## Security Principles

TStack security behavior follows these rules:

- No secret values in logs, reports, SARIF, or evidence bundles
- No SSH execution without explicit future approval controls
- No deployment without human approval
- No untrusted plugin execution without trust policy checks
- No weakening of security gates to make tests pass
- Evidence must be preserved for release decisions

## Current Boundaries

Some TStack systems are intentionally plan-only:

- SSH automation
- Agentic deployment
- Creation OS execution
- Desktop OS control
- File organization

These modules may create plans, reports, and approval requests, but they must not execute sensitive actions unless an explicit approved executor exists.

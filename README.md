# TStack

**TStack** is the T Technology Research Lab workflow, project-audit, and safe-remediation system for planning, building, reviewing, testing, securing, and releasing software with evidence-driven engineering controls.

## Purpose

TStack standardizes the complete software lifecycle:

`Idea → Architecture → Development → Review → QA → Security → Release → Maintenance`

It supports web applications, Android apps, Windows software, AI agents, automation systems, and quantitative or trading research projects.

## Core Workflows

- `architect` — requirements, boundaries, data flow, APIs, scalability, and trade-offs
- `build` — implementation planning and production-grade development
- `review` — correctness, maintainability, technical debt, and regression analysis
- `qa` — test strategy, edge cases, acceptance checks, and release confidence
- `security` — threat modelling, secrets, authentication, OWASP, and dependency risks
- `design` — UI/UX, accessibility, responsive behaviour, and brand consistency
- `ship` — versioning, changelog, deployment, rollback, and post-release verification

## Install

TStack requires Python 3.10 or newer.

```bash
git clone https://github.com/mosinlshaikh/tstack.git
cd tstack
python -m pip install -e ".[dev]"
```

## CLI

```bash
tstack --version
tstack list
tstack init my-project
tstack validate
tstack architect
tstack scan .
tstack scan . --format json --output .tstack/audit.json
tstack scan . --fail-on review
tstack fix .
tstack fix . --apply
```

## Framework-Aware Scanner

TStack detects and evaluates:

- **Python** — project configuration, dependency manifests, tests, and runtime constraints
- **Node.js** — manifest validity, lockfile, tests, static checks, and engine constraints
- **Android/Kotlin** — Gradle wrapper, manifest, unit and instrumentation tests, SDK configuration, and shrinker rules
- **PHP** — Composer manifest and lockfile, tests, and PHP runtime constraints
- **Go** — module manifest, checksum file, tests, and Go version directive
- **Rust** — Cargo manifest and lockfile, tests, and minimum Rust version

The scanner also checks repository-wide controls, source inventory, embedded-secret patterns, sensitive environment files, oversized source files, CI presence, license, security policy, tests, and dependency reproducibility.

## Safe Remediation

`tstack fix` defaults to a dry run and prepares only reversible, low-risk controls:

- framework-aware `.gitignore`
- `SECURITY.md` responsible-disclosure policy
- minimum-permission GitHub Actions CI workflow

```bash
# Inspect proposed changes without writing files
tstack fix .

# Machine-readable plan
tstack fix . --format json

# Apply only missing controls
tstack fix . --apply
```

Existing files are preserved. Application code, credentials, dependency manifests, lockfiles, and business logic are never modified by the remediation engine. `--force` must be explicitly supplied before a selected existing file may be replaced.

## Audit Verdicts

- `PASS` — no material findings
- `REVIEW` — engineering gaps require review before release
- `HOLD` — critical evidence or accumulated risk blocks release

Use `--fail-on never`, `--fail-on hold`, or `--fail-on review` to control CI exit behaviour.

## Repository Structure

```text
tstack/
├── commands/                 # Source workflow documents
├── docs/                     # Architecture and operating documentation
├── src/tstack/               # Standalone Python package
│   ├── workflows/            # Packaged workflow contracts
│   ├── core.py               # Workflow loading, validation, and initialization
│   ├── scanner.py            # Deterministic repository scanner
│   ├── frameworks.py         # Ecosystem-aware deep checks
│   ├── remediation.py        # Safe remediation planning and application
│   └── cli.py                # Command-line interface
├── tests/                    # Regression, framework, and safety fixtures
├── .github/workflows/        # CI validation
├── pyproject.toml
├── CONTRIBUTING.md
└── README.md
```

## Development Validation

```bash
pytest
tstack validate
tstack scan . --fail-on hold
tstack fix .
```

GitHub Actions validates supported Python versions on every push and pull request to `main`.

## Engineering Principles

1. Evidence before conclusions.
2. No data means no decision.
3. Preserve user data and production stability.
4. Prefer minimal, reversible changes.
5. Security and observability are release requirements.
6. Every release must have validation and rollback steps.

## Status

TStack is under active development by **T Technology Research Lab**. Current release stage: **0.4.0 alpha**.

## License

A license will be selected before the first public stable release.

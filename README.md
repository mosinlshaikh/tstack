# TStack

**TStack** is the T Technology Research Lab workflow system for planning, building, reviewing, testing, securing, and releasing software with AI-assisted engineering.

## Purpose

TStack standardizes the complete software lifecycle:

`Idea → Architecture → Development → Review → QA → Security → Release → Maintenance`

It is designed for web applications, Android apps, Windows desktop software, AI agents, automation systems, and quantitative/trading research projects.

## Core Workflows

- `architect` — requirements, system boundaries, data flow, APIs, scalability and trade-offs
- `build` — implementation planning and production-grade development
- `review` — correctness, maintainability, technical debt and regression analysis
- `qa` — test strategy, edge cases, acceptance checks and release confidence
- `security` — threat modelling, secrets, authentication, OWASP and dependency risks
- `design` — UI/UX, accessibility, responsive behaviour and brand consistency
- `ship` — versioning, changelog, deployment, rollback and post-release verification

## Install the CLI

TStack currently supports Python 3.10 or newer.

```bash
git clone https://github.com/mosinlshaikh/tstack.git
cd tstack
python -m pip install -e ".[dev]"
```

## CLI Usage

```bash
tstack --version
tstack list
tstack architect
tstack review
tstack qa --output qa-workflow.md
tstack ship
```

The current alpha CLI should be executed from inside the TStack repository checkout because workflow definitions are loaded from the `commands/` directory.

## Engineering Principles

1. Evidence before conclusions.
2. No data means no decision.
3. Preserve user data and production stability.
4. Prefer minimal, reversible changes.
5. Security and observability are release requirements.
6. Every release must have validation and rollback steps.

## Repository Structure

```text
tstack/
├── commands/                 # Reusable AI engineering workflows
├── docs/                     # Architecture and operating documentation
├── src/tstack/               # Python CLI package
├── tests/                    # CLI regression tests
├── .github/workflows/        # Repository validation automation
├── pyproject.toml
├── CONTRIBUTING.md
└── README.md
```

## Development Validation

```bash
pytest
tstack list
tstack architect --output /tmp/architect.md
```

GitHub Actions validates Python 3.10, 3.11, and 3.12 on every push and pull request to `main`.

## Status

TStack is under active development by **T Technology Research Lab**. Current release stage: **0.1.0 alpha**.

## License

A license will be selected before the first public stable release.

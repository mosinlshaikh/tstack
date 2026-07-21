# TStack

**TStack** is the T Technology Research Lab evidence-driven workflow and project-audit system for planning, building, reviewing, testing, securing, and releasing software.

## Lifecycle

`Idea → Architecture → Development → Review → QA → Security → Release → Maintenance`

TStack supports web applications, Android apps, Windows software, AI agents, automation systems, and quantitative or trading research projects.

## Capabilities

- Packaged engineering workflows: `architect`, `build`, `review`, `qa`, `security`, `design`, `ship`
- Project initialization through `.tstack/`
- Workflow contract validation
- Deterministic project inventory and fingerprinting
- Language and engineering-control detection
- Secret-pattern heuristics that never print matched credentials
- Markdown and machine-readable JSON audit reports
- CI-compatible PASS, REVIEW, and HOLD verdicts

## Install

TStack requires Python 3.10 or newer.

```bash
git clone https://github.com/mosinlshaikh/tstack.git
cd tstack
python -m pip install -e ".[dev]"
```

## Core Usage

```bash
tstack --version
tstack list
tstack validate
tstack init ./my-project
tstack architect
tstack review --output review-workflow.md
```

## Project Audit Engine

Scan a repository and print a Markdown audit:

```bash
tstack scan .
```

Generate JSON for automation:

```bash
tstack scan . --format json --output .tstack/audit.json
```

Control CI behavior:

```bash
# Non-zero only for HOLD
tstack scan . --fail-on hold

# Non-zero for REVIEW or HOLD
tstack scan . --fail-on review

# Always return zero while still producing a report
tstack scan . --fail-on never
```

Exit code `3` means the selected risk threshold was reached. A critical finding or risk score of 60 or higher produces `HOLD`.

## Scanner Boundaries

The scanner is deterministic and dependency-free. It excludes common generated directories, skips symlinks, caps file count and individual file size, and records a SHA-256 project fingerprint. Secret checks are heuristic indicators, not proof; all findings require verification before remediation.

## Engineering Principles

1. Evidence before conclusions.
2. No data means no decision.
3. Preserve user data and production stability.
4. Prefer minimal, reversible changes.
5. Security and observability are release requirements.
6. Every release requires validation and rollback steps.
7. Critical uncertainty produces HOLD, not fabricated confidence.

## Repository Structure

```text
tstack/
├── commands/                 # Human-readable workflow sources
├── docs/                     # Architecture and operating documentation
├── src/tstack/               # Packaged CLI, workflow, and scanner engines
├── tests/                    # Regression and scanner contract tests
├── .github/workflows/        # Multi-version CI validation
├── pyproject.toml
├── CONTRIBUTING.md
└── README.md
```

## Development Validation

```bash
pytest
tstack validate
tstack scan . --format json --fail-on never
```

GitHub Actions validates supported Python versions on pushes and pull requests to `main`.

## Status

TStack is under active development by **T Technology Research Lab**. Current release stage: **0.2.0 alpha**.

## License

A license will be selected before the first public stable release.

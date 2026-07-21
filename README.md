# TStack

**TStack** is the T Technology Research Lab evidence-driven engineering CLI for architecture workflows, repository auditing, framework-aware checks, policy enforcement, safe remediation, baselines, and release gates.

## Lifecycle

`Idea → Architecture → Development → Review → QA → Security → Release → Maintenance`

## Install

TStack requires Python 3.10 or newer.

```bash
git clone https://github.com/mosinlshaikh/tstack.git
cd tstack
python -m pip install -e ".[dev]"
```

## Core Commands

```bash
tstack --version
tstack init my-project
tstack validate
tstack architect
tstack scan .
tstack fix .
tstack fix . --apply
```

## Policy as Code

Create `.tstack/policy.json`:

```bash
tstack policy-init .
```

Default policy:

```json
{
  "fail_on": "critical",
  "max_risk_score": 59,
  "allow_rules": [],
  "allow_paths": []
}
```

Allowlisted findings remain visible in the audit trail but do not block the policy gate.

## Baselines and Scan Diffs

Capture accepted existing findings:

```bash
tstack baseline . --output .tstack/baseline.json
```

Detect only new and resolved findings:

```bash
tstack diff . --baseline .tstack/baseline.json
tstack diff . --baseline .tstack/baseline.json --format json --fail-on-new
```

`--fail-on-new` exits with code `4` when new findings are introduced.

## SARIF and GitHub Code Scanning

```bash
tstack scan . --format sarif --output .tstack/tstack.sarif --fail-on never
```

The SARIF output is compatible with GitHub code-scanning upload workflows. Secret values are never included in findings or SARIF messages.

## Framework-Aware Scanner

TStack evaluates:

- Python — project metadata, dependencies, tests, and runtime constraints
- Node.js — package validity, lockfile, tests, static checks, and engine constraints
- Android/Kotlin — Gradle wrapper, manifest, tests, SDK configuration, and shrinker rules
- PHP — Composer metadata, lockfile, tests, and PHP constraints
- Go — module metadata, checksums, tests, and version directive
- Rust — Cargo metadata, lockfile, tests, and minimum toolchain version

It also checks repository controls, embedded-secret patterns, environment files, CI, licensing, security policy, test presence, oversized files, and reproducible dependencies.

## Safe Remediation

Dry run by default:

```bash
tstack fix .
```

Apply reversible controls:

```bash
tstack fix . --apply
```

The remediation engine can generate `.gitignore`, `SECURITY.md`, and framework-aware GitHub Actions CI. It does not modify application source, credentials, dependency manifests, or lockfiles.

## Verdicts and Exit Codes

- `PASS` — no material release blocker
- `REVIEW` — engineering gaps require review
- `HOLD` — critical evidence or accumulated risk blocks release
- Exit `0` — command passed
- Exit `1` — invalid input or operational error
- Exit `2` — workflow contract validation failed
- Exit `3` — policy or scan release gate failed
- Exit `4` — baseline diff introduced new findings

## Repository Structure

```text
tstack/
├── commands/
├── docs/
├── src/tstack/
│   ├── workflows/
│   ├── core.py
│   ├── scanner.py
│   ├── frameworks.py
│   ├── remediation.py
│   ├── policy.py
│   └── cli.py
├── tests/
├── .github/workflows/
├── pyproject.toml
└── README.md
```

## Validation

```bash
pytest
tstack validate
tstack scan . --fail-on hold
tstack scan . --format sarif --output .tstack/tstack.sarif --fail-on never
```

## Status

Current release stage: **0.5.0 alpha**.

## License

A public license will be selected before the first stable release.

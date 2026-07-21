# TStack

**TStack** is the T Technology Research Lab evidence-driven engineering CLI for architecture workflows, repository auditing, framework-aware checks, policy enforcement, safe remediation, extensible rules, and secure releases.

`Idea → Architecture → Development → Review → QA → Security → Release → Maintenance`

## Install

TStack requires Python 3.10 or newer.

```bash
git clone https://github.com/mosinlshaikh/tstack.git
cd tstack
python -m pip install -e ".[dev]"
```

## Core commands

```bash
tstack --version
tstack init my-project
tstack validate
tstack architect
tstack scan .
tstack fix .
tstack fix . --apply
```

## Policy, baselines, and SARIF

```bash
tstack policy-init .
tstack baseline . --output .tstack/baseline.json
tstack diff . --baseline .tstack/baseline.json --fail-on-new
tstack scan . --format sarif --output .tstack/tstack.sarif --fail-on never
```

Policy allowlists keep suppressed findings visible in the audit trail. Baseline diff exits with code `4` when new findings are introduced. SARIF output is suitable for GitHub Code Scanning and never includes matched secret values.

## Framework-aware scanner

TStack evaluates Python, Node.js, Android/Kotlin, PHP, Go, and Rust projects. It checks manifests, lockfiles, tests, runtime constraints, CI, licensing, security policy, embedded-secret patterns, environment files, oversized sources, and reproducible dependency controls.

## Extensible rules

Projects can add non-executable JSON rules under `.tstack/rules/`. Installed Python packages can register scanners through the `tstack.rules` entry-point group.

Projects may enforce `.tstack/plugin-trust.json` in `allowlist` mode. Installed plugins are matched by entry-point name and deterministic integrity **before their Python code is loaded**. See `docs/PLUGINS.md` and `docs/SUPPLY_CHAIN.md`.

## Safe remediation

```bash
tstack fix .             # dry run
tstack fix . --apply     # create reversible missing controls
```

The remediation engine can generate `.gitignore`, `SECURITY.md`, and framework-aware GitHub Actions CI. It does not modify application source, credentials, dependency manifests, or lockfiles.

## Supply-chain release security

```bash
tstack sbom --output dist/sbom.cdx.json
tstack manifest dist --checksums
tstack verify dist
```

TStack produces a CycloneDX SBOM, deterministic SHA-256 artifact manifest, standard checksum file, and tamper verification. Tagged GitHub releases run tests, build wheel/source distributions, verify metadata, generate GitHub artifact attestations, and upload the complete release bundle.

## Verdicts and exit codes

- `PASS` — no material release blocker
- `REVIEW` — engineering gaps require review
- `HOLD` — critical evidence or accumulated risk blocks release
- Exit `0` — command passed
- Exit `1` — invalid input or operational error
- Exit `2` — workflow validation failed
- Exit `3` — policy or scan release gate failed
- Exit `4` — baseline diff introduced new findings
- Exit `5` — release artifact verification failed

## Repository structure

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
│   ├── plugins.py
│   ├── supplychain.py
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
tstack sbom --output /tmp/tstack-sbom.json
```

## Status

Current release stage: **0.7.0 alpha**.

## License

A public license will be selected before the first stable release.

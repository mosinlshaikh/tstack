# TStack

**TStack** is the T Technology Research Lab evidence-driven engineering CLI for architecture workflows, repository auditing, framework-aware checks, policy enforcement, safe remediation, extensible rules, engineering knowledge packs, automation governance, and secure releases.

```text
Idea -> Architecture -> Development -> Review -> QA -> Security -> Release -> Maintenance
```

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

## Knowledge Packs

TStack currently includes **55 programming language knowledge packs**. Each pack follows the same governance structure:

- `overview`
- `security`
- `performance`
- `testing`
- `production`

Useful commands:

```bash
tstack knowledge list
tstack knowledge stats
tstack knowledge show language-python
tstack knowledge topic language-python security
tstack knowledge validate
```

Machine-readable output:

```bash
tstack knowledge stats --format json
tstack knowledge list --format json
```

## Automation Governance

TStack includes an automation capability registry so SSH, plugins, knowledge, and release automation have explicit safety boundaries.

```bash
tstack automation list
tstack automation show ssh-plan
tstack automation validate
```

Current automation stance:

- SSH automation is **plan-only**.
- TStack does not open SSH connections.
- Automatic plugin installation is blocked.
- Executable Python rule plugins require trust controls.
- Release automation verifies artifacts but does not deploy them.

## SSH Planning

TStack can create policy-checked SSH command plans without executing remote commands.

```bash
tstack ssh init .
tstack ssh plan production-api "systemctl status app" --policy .tstack/ssh-policy.json
```

The SSH planner is intentionally conservative:

- No remote connection is opened.
- No command is executed.
- Targets and commands must be allowlisted.
- Dangerous command patterns are blocked.
- Human approval remains required.

## Policy, Baselines, and SARIF

```bash
tstack policy-init .
tstack baseline . --output .tstack/baseline.json
tstack diff . --baseline .tstack/baseline.json --fail-on-new
tstack scan . --format sarif --output .tstack/tstack.sarif --fail-on never
```

Policy allowlists keep suppressed findings visible in the audit trail. Baseline diff exits with code `4` when new findings are introduced. SARIF output is suitable for GitHub Code Scanning and never includes matched secret values.

## Framework-Aware Scanner

TStack evaluates Python, Node.js, Android/Kotlin, PHP, Go, and Rust projects. It checks manifests, lockfiles, tests, runtime constraints, CI, licensing, security policy, embedded-secret patterns, environment files, oversized sources, and reproducible dependency controls.

## Extensible Rules

Projects can add non-executable JSON rules under `.tstack/rules/`. Installed Python packages can register scanners through the `tstack.rules` entry-point group.

Projects may enforce `.tstack/plugin-trust.json` in `allowlist` mode. Installed plugins are matched by entry-point name and deterministic integrity before Python plugin code is loaded. See `docs/PLUGINS.md` and `docs/SUPPLY_CHAIN.md`.

## Safe Remediation

```bash
tstack fix .             # dry run
tstack fix . --apply     # create reversible missing controls
```

The remediation engine can generate `.gitignore`, `SECURITY.md`, and framework-aware GitHub Actions CI. It does not modify application source, credentials, dependency manifests, or lockfiles.

## Supply-Chain Release Security

```bash
tstack sbom --output dist/sbom.cdx.json
tstack manifest dist --checksums
tstack verify dist
tstack trust-gate dist --repository mosinlshaikh/tstack --commit <FULL_SHA>
```

TStack can produce CycloneDX SBOMs, deterministic dual-hash release manifests, checksum files, trust-gate reports, reproducible-build checks, and evidence bundles.

## Verdicts and Exit Codes

- `PASS`: no material release blocker.
- `REVIEW`: engineering gaps require review.
- `HOLD`: critical evidence or accumulated risk blocks release.
- `0`: command passed.
- `1`: invalid input or operational error.
- `2`: workflow validation failed.
- `3`: policy or scan release gate failed.
- `4`: baseline diff introduced new findings.
- `5`: release artifact verification failed.
- `6`: trust-gate failure.
- `7`: reproducible-build verification failure.
- `8`: release-check failure.
- `10`: evidence-bundle verification failure.
- `11`: decision-plan review or hold result.
- `12`: knowledge validation failure.
- `13`: SSH automation plan blocked by policy.
- `14`: automation registry validation failure.

## Repository Structure

```text
tstack/
|-- commands/
|-- docs/
|-- knowledge/
|   |-- index.json
|   `-- languages/
|-- src/tstack/
|   |-- workflows/
|   |-- automation.py
|   |-- cli.py
|   |-- knowledge.py
|   |-- scanner.py
|   |-- ssh.py
|   `-- supplychain.py
|-- tests/
|-- .github/workflows/
|-- pyproject.toml
`-- README.md
```

## Validation

```bash
pytest
tstack validate
tstack knowledge validate
tstack automation validate
tstack scan . --fail-on hold
```

## Status

Current release stage: **0.17.0 alpha**.

## License

A public license will be selected before the first stable release.

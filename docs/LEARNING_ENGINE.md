# TStack Learning Engine

TStack v0.14.0 adds an explainable, local, human-in-the-loop learning engine.

## What it learns

- recurring rule IDs and affected paths
- occurrence counts
- severity and last remediation
- explicit human feedback: accepted, rejected, or resolved
- ranked recommendations based on recurrence, severity, and feedback

## What it does not do

- no neural-network training
- no autonomous source-code modification
- no automatic deployment or shell/SSH execution
- no secret collection
- no internet upload
- no silent policy changes

The memory remains local at `.tstack/learning-memory.json`.

## Usage

Generate a JSON scan report:

```bash
tstack scan . --format json --output .tstack/latest-scan.json --fail-on never
```

Ingest evidence repeatedly:

```bash
tstack-learn ingest .tstack/latest-scan.json
```

Record a human outcome:

```bash
tstack-learn feedback QA001 --outcome resolved
```

Generate ranked recommendations:

```bash
tstack-learn recommend --output .tstack/recommendations.json
```

## Safety model

Learning may change recommendation priority only. Any remediation, code change, release, or deployment still requires an explicit engineering workflow and human approval.

# TStack Release Trust Gate

TStack combines integrity, provenance prerequisites, and release metadata into one deterministic gate.

## Command

```bash
tstack trust-gate dist \
  --repository mosinlshaikh/tstack \
  --workflow .github/workflows/release.yml \
  --commit <FULL_40_CHARACTER_COMMIT_SHA>
```

Machine-readable output:

```bash
tstack trust-gate dist \
  --repository mosinlshaikh/tstack \
  --commit <FULL_SHA> \
  --format json \
  --output dist/trust-gate.json
```

Strict attestation-receipt mode:

```bash
tstack trust-gate dist \
  --repository mosinlshaikh/tstack \
  --commit <FULL_SHA> \
  --require-attestation-receipt
```

This mode requires `dist/attestation-verification.json`, created only after an external attestation verifier has successfully checked the release artifact.

## Gate checks

- Release manifest is structurally valid.
- Every artifact matches size, SHA-256, and SHA3-256.
- `checksums.sha256` exists.
- `checksums.sha3-256` exists.
- CycloneDX `sbom.cdx.json` exists.
- Repository identity uses `owner/name` form.
- Workflow identity is under `.github/workflows/`.
- Commit identity is a full 40-character SHA.
- Optional attestation verification receipt exists.

## Exit codes

- `0`: trust gate PASS
- `6`: trust gate HOLD
- `1`: invalid input or operational failure

## Attestation verification

The report generates a `gh attestation verify` command scoped to the expected repository and release workflow. Hashes prove byte integrity; attestation proves build identity and provenance. Both layers are required for a high-assurance release.

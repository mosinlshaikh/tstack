# Tamper-Evident Release Evidence Bundles

TStack v0.13.0 can seal a release evidence directory into a deterministic bundle containing SHA-256, SHA3-256, and a SHA3-256 Merkle root.

## Create

```bash
tstack-evidence create dist \
  --repository mosinlshaikh/tstack \
  --commit <FULL_COMMIT_SHA>
```

This writes `dist/evidence-bundle.json`. Every regular file below `dist/` is recorded by relative path, byte size, SHA-256, and SHA3-256. The bundle file itself and verification output are excluded to avoid self-reference.

## Verify

```bash
tstack-evidence verify dist \
  --output dist/evidence-verification.json
```

Verification checks every recorded file, both digests, byte size, and the canonical Merkle root. A modified or missing file produces exit code `10`.

## Why a Merkle root

The root is a compact cryptographic commitment to the complete ordered evidence set. Changing a report, SBOM, checksum file, provenance receipt, or release decision changes its leaf and therefore changes the root.

The Merkle root proves integrity, not publisher identity. Official releases should still use GitHub/Sigstore attestations and verify the expected repository, workflow, and source commit.

## Recommended evidence set

- `manifest.json`
- `checksums.sha256`
- `checksums.sha3-256`
- `sbom.cdx.json`
- `attestation-verification.json`
- `repro-result.json`
- `release-decision.json`
- scanner and policy reports

## Final trust chain

```text
Artifact hashes
    ↓
SBOM + scan + policy evidence
    ↓
Reproducible-build result
    ↓
Sigstore/GitHub provenance receipt
    ↓
Release decision
    ↓
Merkle-sealed evidence bundle
```

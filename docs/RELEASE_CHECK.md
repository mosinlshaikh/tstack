# TStack Release Check

`release-check` combines the project policy, artifact integrity, independent reproducibility, and provenance trust gates into one fail-closed release decision.

```bash
tstack release-check \
  --project . \
  --release dist \
  --rebuilt dist-rebuilt \
  --repository mosinlshaikh/tstack \
  --workflow .github/workflows/release.yml \
  --commit <FULL_40_CHARACTER_COMMIT_SHA> \
  --output dist/release-decision.md
```

The default requires a valid `attestation-verification.json` receipt. Development-only evaluation can bypass that requirement with `--allow-missing-attestation`; official releases must not use that option.

## Stages

1. Project scan and policy evaluation.
2. Dual-hash artifact manifest verification.
3. Independent rebuilt artifact comparison.
4. Repository, workflow, commit, SBOM, checksums, and attestation trust gate.

Every stage must pass. Any failure produces `HOLD` and exit code `8`.

Machine-readable output:

```bash
tstack release-check \
  --rebuilt dist-rebuilt \
  --repository mosinlshaikh/tstack \
  --commit <FULL_SHA> \
  --format json \
  --output dist/release-decision.json
```

The decision report is evidence, not a cryptographic signature. The underlying GitHub/Sigstore attestation remains the cryptographic provenance proof.

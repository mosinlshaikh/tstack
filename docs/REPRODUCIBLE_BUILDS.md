# Reproducible Builds and Provenance Receipts

TStack v0.10.0 adds two independent release-security controls:

1. Byte-for-byte comparison of official and independently rebuilt artifacts.
2. GitHub/Sigstore attestation verification with a machine-readable receipt.

## Independent rebuild comparison

Build the same source commit in a separate clean environment, then compare the release directories:

```bash
tstack repro-verify dist-official dist-rebuilt --output repro-result.json
```

The gate compares both SHA-256 and SHA3-256 for matching wheel, source archive, and ZIP filenames. Exit code `7` means the build is not reproducible or an expected artifact is missing.

A mismatch does not automatically prove malicious behavior. Timestamps, archive ordering, generated metadata, toolchain versions, and locale can all break reproducibility. The correct response is HOLD until the difference is explained and removed.

## Attestation verification receipt

Use GitHub CLI to cryptographically verify the artifact against the expected repository and signer workflow:

```bash
tstack attestation-verify \
  dist/ttrl_tstack-0.10.0-py3-none-any.whl \
  --repository mosinlshaikh/tstack \
  --workflow .github/workflows/release.yml \
  --source-digest <FULL_COMMIT_SHA>
```

The command executes `gh attestation verify` with JSON output, signer-workflow enforcement, source-digest enforcement, and self-hosted-runner denial by default. It writes `attestation-verification.json` beside the artifact.

## Final trust gate

```bash
tstack trust-gate dist \
  --repository mosinlshaikh/tstack \
  --workflow .github/workflows/release.yml \
  --commit <FULL_COMMIT_SHA> \
  --require-attestation-receipt
```

The receipt must match the expected artifact filename, repository, workflow, schema, and contain at least one cryptographically verified attestation result.

## Trust model

```text
Source commit
  -> clean independent rebuild
  -> SHA-256 + SHA3-256 byte comparison
  -> GitHub/Sigstore provenance verification
  -> repository + workflow + source commit binding
  -> SBOM + policy + release trust gate
  -> PASS / HOLD
```

The receipt is not a substitute for signature verification. It is generated only after the GitHub CLI successfully verifies the signed attestation and identity constraints.

# TStack Cryptography Architecture

## Design rule

A hash proves that bytes changed. It does not prove who produced the bytes. TStack therefore separates:

1. **Integrity** — SHA-256 and SHA3-256 digests.
2. **Authenticity and provenance** — GitHub/Sigstore artifact attestations.
3. **Trust policy** — repository, workflow, commit, and publisher identity verification.

## Dual-hash manifest

`tstack manifest dist --checksums` produces:

- `manifest.json` using `tstack-release-manifest/v2`
- `checksums.sha256`
- `checksums.sha3-256`

Verification succeeds only when file size, SHA-256, and SHA3-256 all match. Version 1 SHA-256-only manifests remain readable for backward compatibility.

Dual hashing provides algorithm diversity. It is not a substitute for signatures or attestations.

## Which primitive should be used?

- **SHA-256:** mature, widely interoperable, hardware accelerated, and still suitable for release artifact integrity.
- **SHA3-256:** NIST-standardized alternative based on a different construction; useful for algorithm diversity.
- **BLAKE3:** excellent performance and parallelism, but not the primary interoperability choice for TStack release manifests.
- **Ed25519:** digital-signature algorithm for offline publisher signatures; proves possession of a signing key rather than only byte integrity.
- **Sigstore/GitHub attestations:** preferred CI release provenance because they bind artifacts to repository, workflow, commit, and OIDC identity without a long-lived signing key in the repository.

## Recommended verification order

1. Verify the GitHub/Sigstore attestation and expected repository identity.
2. Verify the release manifest and both hashes.
3. Validate the SBOM and policy requirements.
4. Install or execute the artifact only after all gates pass.

## Security boundary

Neither a correct hash nor a valid attestation proves that software is free of vulnerabilities. They prove integrity and origin. TStack scan, policy, tests, and human review remain separate release requirements.

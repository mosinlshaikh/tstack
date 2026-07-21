# TStack Supply-Chain Security

## Release contract

A release build must produce:

- Python wheel and source distribution
- CycloneDX JSON SBOM (`sbom.cdx.json`)
- deterministic artifact manifest (`manifest.json`)
- SHA-256 checksum file (`checksums.sha256`)
- GitHub artifact attestation for every published file

## Local commands

```bash
tstack sbom --output dist/sbom.cdx.json
tstack manifest dist --checksums
tstack verify dist
```

`verify` returns exit code `5` when an artifact is missing or its size/hash differs from the manifest.

## Trusted plugin policy

Installed Python plugins execute code, so projects may enforce pre-load allowlisting with `.tstack/plugin-trust.json`:

```json
{
  "mode": "allowlist",
  "allowed": [
    {
      "name": "company_rules",
      "integrity": "<sha256 entry-point identity>"
    }
  ]
}
```

In allowlist mode, TStack calculates identity from the entry-point name, import target, and installed distribution version. An unmatched plugin is blocked before `entry.load()` executes. Declarative `.tstack/rules/*.json` rules remain project-local and non-executable.

The integrity value is an identity lock, not a publisher signature. GitHub artifact attestations provide cryptographically signed build provenance for official release files. Future stable releases may add Sigstore verification for third-party plugin packages.

## GitHub release workflow

Tagged releases run tests, build distributions, generate SBOM and checksums, verify the manifest, create GitHub attestations, and upload all artifacts to the matching GitHub Release. The workflow uses explicit least-privilege permissions and does not persist checkout credentials.

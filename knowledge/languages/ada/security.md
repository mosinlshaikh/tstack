# Ada Security

Security review for Ada projects must focus on trust boundaries, dependency handling, and risky runtime capabilities.

## Baseline controls

- Keep credentials and private configuration outside source control.
- Validate external input before parsing, storage, shell execution, network calls, or file access.
- Avoid dynamic evaluation unless the threat model explicitly permits it.
- Use maintained libraries for cryptography, protocols, authentication, and serialization.
- Review dependencies, build scripts, and generated artifacts before release.

## Release rule

A Ada project with unreviewed secrets, unsafe input handling, or unknown dependency trust should remain on HOLD.

# COBOL Security

Security in COBOL projects depends on clear trust boundaries, careful dependency handling, and review of unsafe runtime features.

## Required practices

- Keep secrets outside source control and generated artifacts.
- Validate all external input before parsing, command execution, database access, or file access.
- Use maintained libraries for crypto, authentication, serialization, and protocol handling.
- Review dynamic execution, shell calls, native extensions, and unsafe memory operations when applicable.
- Lock dependencies or document reproducible dependency resolution.

## TStack review focus

Privilege boundaries, injection risk, file-system access, network calls, dependency trust, and production credentials must be reviewed before release.

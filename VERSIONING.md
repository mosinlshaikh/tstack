# Versioning Policy

TStack uses semantic versioning for releases and explicit schema versions for machine-readable files.

## Release Versions

TStack versions follow:

```text
MAJOR.MINOR.PATCH
```

During alpha development, minor versions may introduce new commands, schemas, and experimental APIs. Stable releases must preserve documented contracts unless a migration path is provided.

## Version Meaning

### Major

Major versions may contain breaking changes.

Examples:

- Removing a public CLI command.
- Changing required policy fields.
- Replacing a schema without backward compatibility.
- Breaking plugin SDK contracts.

### Minor

Minor versions add backward-compatible capabilities.

Examples:

- New CLI command.
- New report format.
- New scanner rule.
- New knowledge pack.
- New optional schema field.

### Patch

Patch versions fix defects without changing documented behavior.

Examples:

- Regression fix.
- Documentation correction.
- Security hardening with compatible behavior.
- Test reliability improvement.

## CLI Compatibility

Stable CLI commands must not change output contracts unexpectedly.

For user-facing text, small wording changes are allowed. For machine-readable formats, schema compatibility rules apply.

## Exit Codes

Exit codes are part of the public contract. Changes require documentation and migration guidance.

Current contract:

- `0`: success.
- `1`: operational or input error.
- `2`: workflow validation failure.
- `3`: scan or policy gate failure.
- `4`: new baseline findings detected.
- `5`: release artifact verification failure.
- `6`: trust-gate failure.
- `7`: reproducible-build verification failure.
- `8`: release-check failure.
- `10`: evidence-bundle verification failure.
- `11`: decision-plan review or hold result.
- `12`: knowledge validation failure.
- `13`: SSH automation plan blocked by policy.
- `14`: automation registry validation failure.
- `15`: execution plan is blocked by approval, risk, or executor policy.
- `16`: bug report found review or hold findings.

## Schema Versioning

Machine-readable files must declare a schema where practical.

Versioned schemas include:

- Release manifest.
- Evidence bundle.
- Attestation receipt.
- Policy.
- Baseline.
- Knowledge index.
- Plugin rules.
- Automation registry.

Schema changes must be additive when possible. Breaking schema changes require a new schema identifier.

## Knowledge Pack Versioning

Knowledge packs have their own versions because they may update independently from TStack core.

Knowledge pack updates should identify:

- Pack id.
- Pack version.
- Supported TStack schema version.
- Topics added.
- Topics changed.
- Rules or recommendations changed.

## Plugin Compatibility

Plugin compatibility is defined by the plugin SDK version and rule schema version.

TStack must reject incompatible plugins clearly instead of loading them with undefined behavior.

## Deprecation Policy

Deprecations should include:

- Replacement command or field.
- First version where deprecation appears.
- Earliest version where removal may happen.
- Migration guidance.

Stable removals should avoid surprise. Alpha releases may move faster, but breaking changes still need clear documentation.

## Release Readiness

A version should not be released unless:

- Tests pass.
- Documentation is updated.
- Changelog or release notes are prepared.
- Release artifacts are generated.
- Trust and evidence checks pass for official releases.

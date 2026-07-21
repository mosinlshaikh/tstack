# TStack RFC Process

RFCs document important architecture and product decisions before they become permanent behavior.

Use an RFC when a change affects:

- Public CLI behavior.
- Schemas or report formats.
- Plugin SDK contracts.
- Release trust model.
- Knowledge pack format.
- Security boundaries.
- Backward compatibility.
- Long-term architecture.

Small bug fixes and documentation-only updates usually do not require an RFC.

## RFC Lifecycle

```text
Draft -> Review -> Accepted -> Implemented -> Superseded
```

### Draft

The idea is written down with motivation, design, risks, and alternatives.

### Review

Maintainers and contributors evaluate the proposal. Security and compatibility concerns must be resolved before acceptance.

### Accepted

The project agrees with the direction. Accepted does not mean implemented.

### Implemented

The change has code, tests, documentation, and release notes where needed.

### Superseded

The RFC has been replaced by a newer decision.

## RFC Numbering

Use four-digit identifiers:

```text
RFC-0001-title.md
RFC-0002-title.md
```

Numbers are assigned in merge order.

## Recommended Template

```markdown
# RFC-0000: Title

## Status

Draft

## Summary

Briefly describe the proposal.

## Motivation

Explain the problem and why it matters.

## Design

Describe the proposed behavior, interfaces, schemas, or architecture.

## Security Considerations

Identify trust boundaries, sensitive data, and failure modes.

## Compatibility

Describe effects on CLI, schemas, plugins, and existing users.

## Alternatives

List options considered and why they were not selected.

## Rollout Plan

Explain implementation, testing, documentation, and migration.

## Open Questions

List unresolved decisions.
```

## Review Standard

An RFC should be accepted only when it is:

- Evidence-based.
- Testable.
- Secure by default.
- Compatible or clearly versioned.
- Maintainable.
- Aligned with the TStack Constitution.

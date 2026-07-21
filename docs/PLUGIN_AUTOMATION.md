# Plugin Automation

TStack has plugin architecture and plugin trust controls, but it does not auto-install or auto-run arbitrary plugins.

## Current Position

Supported:

- Declarative project rules.
- Installed Python rule plugins.
- Plugin attribution in scan results.
- Trust allowlist model.
- Pre-load blocking for untrusted executable plugins.

Not supported:

- Automatic plugin installation.
- Running every discovered plugin by default.
- Installing plugins from remote URLs without review.
- Executing plugin code without trust policy.

## Required Safety Model

Future plugin automation must enforce:

- Explicit install approval.
- Version pinning.
- Integrity or trusted publisher check.
- Permission declaration.
- Audit trail.
- Disable/remove path.
- No hidden network or filesystem access.

The default stance is conservative: plugins extend TStack, but they must not weaken the evidence and trust model.

# Automation Registry

TStack automation is intentionally explicit. The registry records what the tool can automate, what remains plan-only, and which capabilities require trust and approval.

## Commands

List all capabilities:

```bash
tstack automation list
```

Machine-readable output:

```bash
tstack automation list --format json
```

Show one capability:

```bash
tstack automation show ssh-plan
```

Validate the registry:

```bash
tstack automation validate
```

## Safety model

Automation capabilities are classified by:

- `status`: whether the capability is available, trust-gated, or blocked.
- `mode`: how the automation behaves.
- `execution_allowed`: whether the capability can execute anything.
- `approval_required`: whether a human must approve use.
- `trust_required`: whether a trust policy or equivalent review is required.
- `safety_boundary`: the exact limit TStack must not cross.

## Current boundaries

- SSH is plan-only. TStack does not open remote connections.
- Automatic plugin installation is blocked.
- Project JSON rules are non-executable.
- Installed Python plugins require trust policy review before use.
- Release automation verifies artifacts but does not publish or deploy them.

The registry is a governance layer. It prevents hidden automation from appearing in the product without a documented safety contract.

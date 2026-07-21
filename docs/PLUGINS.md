# TStack Plugin System

TStack supports two extension models.

## 1. Project declarative rules

Create `.tstack/rules/*.json`:

```json
{
  "rules": [
    {
      "id": "TTRL_LEGACY",
      "severity": "high",
      "title": "Legacy code requires migration",
      "path_regex": "^legacy/",
      "remediation": "Move the module behind a maintained interface."
    }
  ]
}
```

Declarative rules inspect relative paths only. They do not execute project code or include file contents in evidence. Rule IDs must be uppercase namespaced identifiers. Invalid schemas fail the scan closed.

## 2. Installed Python plugins

Packages register an entry point in the `tstack.rules` group:

```toml
[project.entry-points."tstack.rules"]
company_rules = "company_tstack:Rules"
```

The object must expose `name`, `version`, and:

```python
def scan(root: Path, relative_files: frozenset[str]):
    return [
        {
            "rule_id": "ACME001",
            "severity": "high",
            "title": "Required control missing",
            "path": None,
            "evidence": "A deterministic control check failed.",
            "remediation": "Add the required control."
        }
    ]
```

Supported severities are `low`, `medium`, `high`, and `critical`.

## Trust model

Python plugins execute with the permissions of the TStack process. Install only reviewed packages from trusted publishers. Project declarative rules are preferred for simple repository policies because they are non-executable.

Each loaded plugin receives deterministic integrity metadata in scan reports. This is an identity/change indicator, not a cryptographic publisher signature. Real package signing and trust-store verification remain a future stable-release requirement.

Plugin failures are fatal by design. TStack does not silently ignore malformed rules or invalid findings because that would create false release confidence.

# TStack Engineering Knowledge Graph

The Engineering Knowledge Graph (EKG) converts a repository into deterministic nodes and relationships for impact analysis.

## Build

```bash
tstack-graph build .
```

Default output:

```text
.tstack/knowledge-graph.json
```

## Impact analysis

```bash
tstack-graph impact src/tstack/scanner.py
```

The result includes direct dependents, transitive impact, affected tests, and a LOW/MEDIUM/HIGH blast-radius classification.

## Summary and visualization

```bash
tstack-graph summary
tstack-graph dot --output .tstack/knowledge-graph.dot
```

Graphviz can render the DOT file separately.

## Current extraction scope

- Source, test, and important configuration nodes
- Python import relationships using the standard-library AST
- Test-to-source naming relationships
- Deterministic graph fingerprint
- Reverse dependency traversal

## Trust boundary

The graph is evidence, not certainty. Dynamic imports, reflection, generated code, runtime service calls, and external systems may not be visible. Unknown relationships must not be presented as proven impact.

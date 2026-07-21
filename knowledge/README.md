# TStack Knowledge Framework

The `knowledge/` directory contains versioned engineering knowledge packs used by TStack's knowledge, language, and decision systems.

Knowledge packs are not a dump of model internals. They are curated, reviewable engineering materials that can be indexed, tested, and linked to project evidence.

## Current Coverage

TStack currently includes **55 programming language packs**. Every language pack includes:

- `overview`
- `security`
- `performance`
- `testing`
- `production`

Check coverage with:

```bash
tstack knowledge stats
tstack knowledge validate
```

## Goals

- Provide maintainable engineering guidance.
- Keep knowledge separate from the core runtime.
- Make recommendations traceable.
- Support language, framework, security, architecture, and DevOps packs.
- Integrate with the knowledge graph over time.

## Directory Model

```text
knowledge/
|-- README.md
|-- index.json
|-- languages/
|-- frameworks/
|-- architecture/
|-- security/
|-- databases/
|-- devops/
|-- ai/
|-- testing/
`-- examples/
```

## Knowledge Pack Standard

Each pack must define:

- Pack id.
- Pack title.
- Pack version.
- Topic list.
- Supported TStack schema version.
- Intended audience.
- Limitations.
- Review status.
- Quality gates.

## Content Rules

Knowledge content must distinguish:

- Facts.
- Best practices.
- TStack opinions.
- Security requirements.
- Framework-specific guidance.
- Assumptions.
- Known limitations.

## Quality Bar

Before a pack becomes stable, it should have:

- Clear structure.
- Reviewed examples.
- Security guidance where applicable.
- Testing guidance where applicable.
- Production guidance where applicable.
- Index metadata.
- Validation through `tstack knowledge validate`.

## Roadmap

Next knowledge milestones:

- Promote high-value language packs from `draft` to `review`.
- Add framework packs for Python, JavaScript/TypeScript, Java/Kotlin, Go, and Rust ecosystems.
- Add architecture, security, database, DevOps, and AI engineering packs.
- Link knowledge packs into the Engineering Knowledge Graph.

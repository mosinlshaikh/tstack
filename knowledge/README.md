# TStack Knowledge Framework

The `knowledge/` directory contains versioned engineering knowledge packs used by TStack's future knowledge, language, and decision systems.

Knowledge packs are not a dump of model internals. They are curated, reviewable engineering materials that can be indexed, tested, and linked to project evidence.

## Goals

- Provide maintainable engineering guidance.
- Keep knowledge separate from the core runtime.
- Make recommendations traceable.
- Support language, framework, security, architecture, and DevOps packs.
- Integrate with the knowledge graph over time.

## Directory Model

Planned structure:

```text
knowledge/
├── README.md
├── index.json
├── languages/
├── frameworks/
├── architecture/
├── security/
├── databases/
├── devops/
├── ai/
├── testing/
└── examples/
```

The initial commit creates the framework and index. Individual packs should be added in focused follow-up changes.

## Knowledge Pack Standard

Each pack should define:

- Pack id.
- Pack title.
- Pack version.
- Topic list.
- Supported TStack schema version.
- Intended audience.
- Limitations.
- Review status.

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

## Roadmap

Initial planned packs:

- Python.
- Go.
- Rust.
- Java.
- Kotlin.
- JavaScript.
- TypeScript.
- SQL.
- DevOps foundations.
- Security foundations.
- Architecture patterns.

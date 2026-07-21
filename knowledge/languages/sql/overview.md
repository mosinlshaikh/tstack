# SQL Overview

SQL is the standard language for querying and managing relational data.

## Strengths

- Declarative data access.
- Strong fit for transactional systems.
- Mature database engines and tooling.
- Central to reporting, analytics, and business applications.

## Tradeoffs

- Dialects differ between database engines.
- Poor schema and index design can cause serious performance issues.
- Migrations need rollback and data-safety planning.

TStack should prefer `REVIEW` when migrations, indexes, backups, or query safety are unclear.

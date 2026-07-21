# SQL Performance

SQL performance depends on schema design, indexes, query shape, statistics, and workload patterns.

## Guidance

- Review query plans for critical queries.
- Add indexes based on workload evidence.
- Avoid N+1 query patterns.
- Test migrations on representative data.
- Monitor slow queries in production.

TStack should raise risk when high-volume tables or critical queries change without plan or benchmark evidence.

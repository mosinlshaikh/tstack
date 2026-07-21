# SQL Testing

SQL changes need tests and migration validation.

## Test Layers

- Migration tests.
- Query behavior tests.
- Data integrity checks.
- Rollback verification where practical.
- Performance checks for critical queries.

TStack should flag migrations without tests, destructive changes without backup evidence, and query changes without representative validation.

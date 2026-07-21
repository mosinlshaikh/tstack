# Java Testing

Java projects should combine unit, integration, contract, and regression tests.

## Common Tooling

- JUnit.
- Mockito or equivalent test doubles.
- Maven or Gradle test tasks.
- Testcontainers for integration tests where appropriate.
- Static analysis and formatting checks.

## TStack Rules

Flag missing tests, CI gaps, missing integration coverage for persistence or messaging boundaries, and release-critical fixes without regression tests.

# C# Overview

C# is a modern managed language used for backend services, desktop apps, games, cloud systems, and enterprise platforms through .NET.

## Strengths

- Strong type system and tooling.
- Mature .NET runtime and libraries.
- Good performance for managed applications.
- Strong enterprise and cloud support.
- Useful async model for I/O-heavy services.

## Tradeoffs

- Runtime and deployment model should be understood clearly.
- Framework choices can hide operational complexity.
- Async misuse can cause deadlocks or thread-pool pressure.

TStack should prefer `REVIEW` when .NET version, tests, dependency strategy, or runtime configuration are unclear.

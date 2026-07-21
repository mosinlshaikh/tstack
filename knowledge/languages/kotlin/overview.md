# Kotlin Overview

Kotlin is a modern JVM language used for Android, backend services, and multiplatform development.

## Strengths

- Concise syntax and null-safety features.
- Strong Android ecosystem support.
- JVM interoperability.
- Coroutines for structured asynchronous work.
- Good fit for domain-focused application code.

## Tradeoffs

- Build performance can require tuning.
- Coroutine misuse can create subtle lifecycle defects.
- Java interoperability can expose nullable or platform-type risks.
- Multiplatform maturity varies by target.

TStack should prefer `REVIEW` when coroutine boundaries, tests, or target versions are unclear.

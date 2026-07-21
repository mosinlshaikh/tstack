# Rust Overview

Rust is a compiled systems language focused on memory safety, performance, and fearless concurrency without a garbage collector.

## Strengths

- Strong memory safety guarantees.
- Excellent performance for systems and backend workloads.
- Strong type system and ownership model.
- Good fit for CLIs, infrastructure, embedded systems, WebAssembly, and high-reliability services.
- Modern package manager and build system through Cargo.

## Tradeoffs

- Learning curve is higher than many application languages.
- Compile times can be significant.
- Ownership and lifetime design require up-front thought.
- Ecosystem maturity varies by domain.

## Architecture Guidance

Use Rust when:

- Memory safety and performance both matter.
- Low-level control is required.
- Reliability matters more than fastest initial development.
- CPU-bound or resource-sensitive workloads are central.

Avoid Rust as the default when:

- The team lacks Rust experience and delivery speed is the top priority.
- The project mostly orchestrates external APIs where a higher-level ecosystem is more productive.
- Library support in the target domain is weak.

## TStack Recommendation Rules

TStack should prefer `REVIEW` when a Rust project lacks tests, `Cargo.lock` for applications, or a declared toolchain/version strategy.

TStack should prefer `HOLD` when unsafe code appears without review evidence in security-sensitive areas.

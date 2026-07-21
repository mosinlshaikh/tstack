# C Overview

C is a low-level systems language used for operating systems, embedded software, libraries, runtimes, and performance-sensitive components.

## Strengths

- Direct memory and hardware control.
- Portable language core.
- Excellent interoperability.
- Small runtime requirements.
- Strong fit for embedded and systems work.

## Tradeoffs

- Manual memory management creates serious safety risk.
- Undefined behavior can produce hard-to-debug failures.
- Toolchain and platform differences matter.
- Security review burden is high.

TStack should prefer `REVIEW` when C projects lack tests, compiler warning flags, static analysis, or sanitizer strategy.

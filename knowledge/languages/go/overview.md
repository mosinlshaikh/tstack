# Go Overview

Go is a compiled language designed for simple syntax, fast builds, efficient concurrency, and reliable network services.

## Strengths

- Strong fit for APIs, CLIs, infrastructure tools, and distributed systems.
- Fast compilation and simple deployment through static binaries.
- Built-in concurrency with goroutines and channels.
- Mature standard library for networking and systems work.
- Clear formatting and tooling conventions.

## Tradeoffs

- Error handling is explicit and can become repetitive without discipline.
- Generics are useful but intentionally limited compared with some languages.
- Runtime safety is strong but does not remove the need for race and resource review.
- Abstractions should stay simple; over-engineered interfaces reduce readability.

## Architecture Guidance

Use Go when:

- Services need high concurrency with operational simplicity.
- Deployment benefits from single binaries.
- Infrastructure, platform, or networking work is central.
- Predictable latency and memory behavior matter.

Avoid Go as the only solution when:

- Heavy numerical computing needs mature vectorized ecosystems.
- Low-level memory control without runtime involvement is required.
- A project depends primarily on a language-specific AI or data ecosystem.

## TStack Recommendation Rules

TStack should prefer `REVIEW` when a Go module lacks `go.sum`, tests, or a Go version directive.

TStack should prefer `HOLD` when release-critical services lack timeout, cancellation, or credential controls.

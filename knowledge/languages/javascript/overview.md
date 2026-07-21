# JavaScript Overview

JavaScript is the core language of the web and is also widely used for server-side, CLI, and automation workloads through Node.js and related runtimes.

## Strengths

- Runs natively in browsers.
- Large ecosystem and fast iteration.
- Strong fit for full-stack and UI-heavy work.
- Event-driven model works well for I/O-bound applications.

## Tradeoffs

- Runtime type errors require strong testing and validation discipline.
- Dependency supply-chain risk is significant.
- Browser and server runtimes have different constraints.
- Build tooling can become complex.

TStack should prefer `REVIEW` when JavaScript projects lack tests, lockfiles, linting, or runtime input validation.

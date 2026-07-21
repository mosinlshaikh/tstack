# TypeScript Overview

TypeScript adds static typing and tooling to JavaScript, supporting frontend, backend, CLI, and full-stack applications.

## Strengths

- Strong developer tooling.
- Better refactoring safety than plain JavaScript.
- Good fit for shared API contracts.
- Works across browser and Node.js ecosystems.
- Large framework ecosystem.

## Tradeoffs

- Types are erased at runtime.
- Build pipelines can become complex.
- Weak type settings reduce value.
- Dependency ecosystems require careful security review.

TStack should prefer `REVIEW` when TypeScript projects lack lockfiles, tests, or a typecheck script.

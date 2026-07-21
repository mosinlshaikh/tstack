# Assembly Overview

Assembly is a low-level architecture-specific language for hardware control, reverse engineering, and performance-critical code. TStack records this as practical engineering guidance for maintainable production work.

## Core engineering model

- Match Assembly to the runtime, team skill, ecosystem, and operational target.
- Keep domain logic separate from platform-specific integration code.
- Prefer idiomatic package, build, and test tooling.
- Document supported versions, runtime assumptions, and deployment constraints.

## Appropriate use

Use Assembly when its ecosystem, runtime model, or deployment environment directly supports the project goal. Avoid choosing it only for novelty.

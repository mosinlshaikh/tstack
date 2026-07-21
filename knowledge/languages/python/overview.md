# Python Overview

Python is a high-level, dynamically typed language used for web services, automation, data engineering, machine learning, scripting, and developer tooling.

## Strengths

- Fast development cycle.
- Large standard library and package ecosystem.
- Strong readability when code style is disciplined.
- Excellent support for automation, backend APIs, data workflows, and AI systems.
- Mature testing and packaging tools.

## Tradeoffs

- Runtime performance is lower than compiled systems languages for CPU-bound workloads.
- Dynamic typing can hide integration defects unless static analysis and tests are used.
- Packaging and dependency resolution require disciplined project setup.
- Concurrency model depends heavily on workload type: I/O-bound, CPU-bound, or external-service-bound.

## Architecture Guidance

Use Python when:

- Developer productivity matters.
- The workload is I/O-bound or orchestrates external systems.
- AI, automation, data, or backend service libraries provide strong leverage.
- Performance-sensitive paths can be isolated, optimized, or moved to native extensions/services.

Avoid Python as the only runtime when:

- Low-latency CPU-bound processing is the primary requirement.
- Memory use must be tightly controlled.
- Startup time is a hard product constraint.
- The target environment has limited Python support.

## Project Quality Signals

A production-grade Python project should usually include:

- `pyproject.toml` or equivalent project metadata.
- Declared supported Python versions.
- Reproducible dependency strategy.
- Automated tests.
- Static analysis or linting.
- Clear package/module layout.
- CI execution across supported Python versions.
- Security handling for secrets, input validation, and dependency review.

## TStack Recommendation Rules

TStack should prefer `REVIEW` when a Python project lacks tests, runtime version constraints, or dependency controls.

TStack should prefer `HOLD` when credential patterns, unsafe deserialization, uncontrolled dynamic execution, or release evidence gaps are found.

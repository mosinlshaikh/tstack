# C++ Security

C++ security depends on memory-safety discipline, safe abstractions, dependency review, and tool-assisted analysis.

## High-Risk Patterns

- Raw owning pointers.
- Use-after-free.
- Buffer overflows.
- Integer overflow.
- Data races.
- Unsafe casts.
- Manual lifetime management across async boundaries.

## Required Controls

- Prefer RAII and safe standard abstractions.
- Use sanitizers where practical.
- Run static analysis.
- Fuzz parsers and untrusted input boundaries.
- Review concurrency and ownership explicitly.

TStack should mark exposed unsafe memory patterns as high risk or `HOLD` depending on blast radius.

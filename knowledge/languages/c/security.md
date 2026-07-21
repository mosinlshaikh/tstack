# C Security

C security requires explicit memory-safety discipline.

## High-Risk Patterns

- Buffer overflows.
- Use-after-free.
- Double free.
- Integer overflow.
- Format-string vulnerabilities.
- Unsafe string and memory functions.
- Unchecked pointer arithmetic.

## Required Controls

- Strict compiler warnings.
- Static analysis.
- Sanitizers where practical.
- Fuzzing for parsers and untrusted input.
- Code review for ownership and lifetime behavior.

TStack should mark memory-unsafe patterns in exposed code paths as high risk or `HOLD` depending on evidence.

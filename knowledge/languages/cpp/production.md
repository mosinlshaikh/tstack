# C++ Production

Production C++ requires explicit build, compiler, dependency, and runtime controls.

## Required Signals

- C++ standard declared.
- Toolchain and target platform documented.
- Build system reproducible enough for release.
- Tests and static analysis in CI.
- Sanitizer strategy documented where practical.
- Release artifacts tied to known commits.

TStack should increase risk when ABI, compiler, dependency, or memory-safety controls are unclear.

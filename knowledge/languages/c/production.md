# C Production

Production C requires explicit toolchain, platform, build, and safety controls.

## Required Signals

- Build system documented.
- Compiler and target platform defined.
- Warning flags enforced.
- Tests and static analysis run in CI.
- Release artifacts are reproducible enough for the target.
- Security review completed for memory and input boundaries.

TStack should increase risk when compiler flags, target platforms, or memory-safety controls are undocumented.

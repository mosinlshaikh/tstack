# Runtime Kernel

TStack Runtime Kernel v1 is the foundation for future real execution.

It introduces:

- capability requests
- request hashes
- human decisions bound to request hashes
- audit events
- explicit execution blocking

```bash
tstack runtime request filesystem.move "Organize Downloads" --target Downloads --format json
tstack runtime decide request.json --approved --approver Mosin --reason "Reviewed plan." --format json
tstack runtime audit request.json --decision decision.json --outcome approved --format json
```

## Boundary

This kernel does not yet move files, run processes, control browsers, launch Blender, build apps, or deploy releases. It creates the policy and audit contract that future executors must pass through.

Agents must request capabilities instead of directly touching the operating system.

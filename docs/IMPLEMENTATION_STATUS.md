# Implementation Status

Every public capability must be labeled honestly.

| Capability | Status | Evidence |
|---|---|---|
| Repository scan | WORKING | `tstack scan .` |
| Policy, baseline, SARIF | WORKING | Policy and SARIF tests |
| Supply-chain manifest/SBOM/trust gate | EXPERIMENTAL | Release-security commands and tests |
| Knowledge packs | EXPERIMENTAL | 55 draft language packs |
| Agent catalog/orchestration | PLAN-ONLY | Generates plans, does not execute agent work |
| Runtime capability request | EXPERIMENTAL | Hash-bound request/decision/audit commands |
| Runtime kernel task vertical slice | EXPERIMENTAL | SQLite task -> signed approval -> filesystem write -> audit -> rollback |
| Capability model registry | WORKING | `tstack capability list`, `tstack capability validate` |
| Sandbox runner | EXPERIMENTAL | Controlled subprocess, not OS/container isolation |
| File inventory and organize plan | WORKING | Inventory and plan commands |
| Transactional file runtime | EXPERIMENTAL | Approved move/undo flow |
| SSH | PLAN-ONLY | No remote connection |
| Desktop OS | PLAN-ONLY | Blueprint only |
| Creation OS | PLAN-ONLY | Blueprint and project planning only |
| Browser control | NOT STARTED | No Playwright worker in repository |
| Blender bridge | NOT STARTED | No add-on or bridge runtime |
| Godot/Unity/Unreal bridges | NOT STARTED | No engine bridge runtime |
| Android builder | NOT STARTED | Environment detection only |
| iOS Mac node | NOT STARTED | Architecture not implemented |
| Local AI providers | NOT STARTED | No inference runtime integration |
| Desktop UI | NOT STARTED | No Tauri/React app |

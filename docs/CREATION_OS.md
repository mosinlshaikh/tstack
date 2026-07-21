# TStack Creation OS

TStack Creation OS is a local-first autonomous software, 3D, game, web, and mobile development platform with human approval gates.

## Product Scope

It is not only an AI assistant. It is designed to coordinate:

- Image to GLB asset creation.
- Blender automation.
- 2D and 3D game building.
- Android app building.
- iOS project preparation and Mac build-node handoff.
- Website and software development.
- Local environment detection.
- Discussion -> planning -> work -> testing -> deployment lifecycle.

## Command

```bash
tstack creation blueprint
tstack creation blueprint --format json
tstack creation plan image-to-glb "Create low-poly GLB from character image"
tstack creation plan android-app "Build medical store app" --format json
```

## Key Rules

- Single-image 3D backside geometry must be marked estimated.
- Blender is the central local 3D engine.
- Godot is the recommended primary local-first game engine.
- Android builds require SDK/JDK/Gradle/ADB readiness.
- Final iOS builds require Mac + Xcode or an approved Mac build node.
- Docker is useful for services, tests, AI workers, and build workers, but visible Blender, GPU-heavy rendering, game editors, emulators, and Xcode must stay native.
- Deployment and signing require explicit approval.

## Practical Build Order

1. Local Creation Core.
2. Blender + GLB.
3. Game Builder.
4. Mobile Builder.
5. Unified Agentic Workspace.

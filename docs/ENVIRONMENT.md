# Environment Manager

The Environment Manager detects local tools required for Creation OS workflows.

It reports what is installed and what is missing. It does not install tools automatically.

## Commands

```bash
tstack environment inspect
tstack environment inspect --profile 3d
tstack environment inspect --profile mobile --format json
```

## Profiles

- `core`: Python and Git.
- `web`: Node.js.
- `devops`: Docker.
- `3d`: Blender.
- `game`: Godot.
- `mobile`: JDK, ADB, Gradle.
- `media`: FFmpeg.

## Safety

Installation requires explicit approval. Admin actions, PATH mutation, SDK installation, and emulator setup must stay behind approval gates.

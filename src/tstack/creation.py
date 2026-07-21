"""Local-first Creation OS blueprint for 3D, games, web, and mobile."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


CREATION_BLUEPRINT_SCHEMA = "tstack-creation-blueprint/v1"


@dataclass(frozen=True)
class CreationPipeline:
    id: str
    name: str
    stages: tuple[str, ...]
    primary_tools: tuple[str, ...]
    approval_gates: tuple[str, ...]
    local_first: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True)
class CreationPlugin:
    id: str
    name: str
    permissions: tuple[str, ...]
    approval_required: bool
    external_api_required: bool = False


PIPELINES: tuple[CreationPipeline, ...] = (
    CreationPipeline(
        "image-to-glb",
        "Image to GLB",
        ("image analysis", "segmentation", "depth estimation", "mesh generation", "mesh cleanup", "UV unwrap", "texture generation", "optional rigging", "GLB validation", "export"),
        ("Blender", "Python", "local vision models", "texture tools"),
        ("source image approval", "estimated geometry warning", "final export approval"),
    ),
    CreationPipeline(
        "blender-bridge",
        "Blender Bridge",
        ("create from image", "generate mesh", "clean topology", "retopology", "UV and texture", "auto rig", "animation", "optimize for mobile", "export GLB/FBX/USD", "validate asset"),
        ("Blender Python API", "Blender CLI", "FFmpeg"),
        ("script execution approval", "asset overwrite approval", "export approval"),
    ),
    CreationPipeline(
        "game-builder",
        "Complete Game Builder",
        ("game design document", "mechanics", "art direction", "assets", "scenes and levels", "controls", "NPCs", "audio", "UI", "save system", "tests", "profiling", "platform builds"),
        ("Godot", "Blender", "local audio tools", "Android SDK"),
        ("engine script approval", "build approval", "store package approval"),
    ),
    CreationPipeline(
        "android-builder",
        "Android App Builder",
        ("project generation", "Kotlin or framework setup", "UI", "APIs", "tests", "lint", "debug APK", "release bundle", "device/emulator validation"),
        ("Android SDK", "Gradle", "JDK", "ADB", "Kotlin", "Jetpack Compose"),
        ("dependency install approval", "signing approval", "device install approval"),
    ),
    CreationPipeline(
        "ios-builder",
        "iOS App Builder",
        ("Swift/SwiftUI project plan", "static checks", "tests", "Mac node handoff", "simulator validation", "archive", "store package"),
        ("Swift", "SwiftUI", "Xcodebuild", "simctl", "Mac build node"),
        ("Mac node approval", "signing approval", "archive approval"),
    ),
    CreationPipeline(
        "environment-manager",
        "Local Environment Manager",
        ("system scan", "tool detection", "version check", "missing dependency plan", "approval", "installation plan", "verification", "environment snapshot"),
        ("Python", "Rust", "PowerShell/Bash", "SQLite"),
        ("installation approval", "admin approval", "PATH mutation approval"),
    ),
)


PLUGINS: tuple[CreationPlugin, ...] = (
    CreationPlugin("blender-bridge", "Blender Bridge", ("read_files", "write_project_files", "run_blender"), True),
    CreationPlugin("godot-bridge", "Godot Bridge", ("read_files", "write_project_files", "run_game_engine"), True),
    CreationPlugin("unity-bridge", "Unity Bridge", ("read_files", "write_project_files", "run_game_engine"), True),
    CreationPlugin("unreal-bridge", "Unreal Bridge", ("read_files", "write_project_files", "run_game_engine"), True),
    CreationPlugin("android-bridge", "Android Bridge", ("read_files", "write_project_files", "build_android", "run_emulator"), True),
    CreationPlugin("xcode-mac-bridge", "Xcode Mac Bridge", ("connect_mac_builder", "build_ios", "sign_ios"), True),
    CreationPlugin("docker-bridge", "Docker Bridge", ("run_containers", "build_images", "manage_volumes"), True),
    CreationPlugin("github-bridge", "GitHub Bridge", ("read_repo", "write_branch", "draft_pr"), True, True),
    CreationPlugin("browser-bridge", "Browser Bridge", ("access_internet", "browser_automation", "download_files"), True),
    CreationPlugin("ffmpeg-bridge", "FFmpeg Bridge", ("read_files", "write_project_files", "process_media"), True),
    CreationPlugin("local-ai-bridge", "Local AI Bridge", ("run_local_model", "read_knowledge", "write_cache"), True),
    CreationPlugin("asset-library", "Asset Library", ("read_assets", "write_project_files"), True),
    CreationPlugin("deployment-bridge", "Deployment Bridge", ("deploy", "publish_artifacts", "manage_release"), True, True),
)


def creation_blueprint() -> dict:
    return {
        "schema": CREATION_BLUEPRINT_SCHEMA,
        "product": "TStack Creation OS",
        "definition": "Local-first autonomous software, 3D, game, web and mobile development platform with human approval gates.",
        "lifecycle": ("discussion", "plan", "work", "check", "local preview", "deployment"),
        "project_types": ("website", "android-app", "ios-app", "desktop-software", "2d-game", "3d-game", "image-to-glb", "3d-character", "animation-video", "custom-project"),
        "pipelines": [asdict(item) for item in PIPELINES],
        "plugins": [asdict(item) for item in PLUGINS],
        "native_host_tools": ("Blender visible UI", "GPU rendering", "Godot editor", "Unity/Unreal editors", "Android emulator", "Xcode Mac node", "desktop control"),
        "docker_tools": ("backend services", "databases", "web builds", "tests", "local AI services", "asset processors", "CI workers"),
        "hard_rules": (
            "single-image 3D backside geometry must be marked estimated",
            "final iOS build requires Mac + Xcode or approved Mac build node",
            "deployment and signing require explicit approval",
            "external APIs are optional plugins and disabled by default",
            "all destructive or publishing actions require approval and rollback plan",
        ),
    }


def creation_blueprint_json() -> str:
    return json.dumps(creation_blueprint(), indent=2, sort_keys=True) + "\n"


def creation_blueprint_markdown() -> str:
    payload = creation_blueprint()
    lines = [
        "# TStack Creation OS",
        "",
        payload["definition"],
        "",
        f"- Project types: {len(payload['project_types'])}",
        f"- Pipelines: {len(payload['pipelines'])}",
        f"- Plugins: {len(payload['plugins'])}",
        "",
        "## Lifecycle",
        "",
        " -> ".join(payload["lifecycle"]),
        "",
        "## Pipelines",
        "",
    ]
    for pipeline in PIPELINES:
        lines.append(f"- `{pipeline.id}` - {pipeline.name}: {', '.join(pipeline.primary_tools)}")
    lines.extend(["", "## Plugin Ecosystem", ""])
    for plugin in PLUGINS:
        lines.append(f"- `{plugin.id}` - {plugin.name}: {', '.join(plugin.permissions)}")
    lines.extend(["", "## Hard Rules", ""])
    lines.extend(f"- {item}" for item in payload["hard_rules"])
    return "\n".join(lines) + "\n"

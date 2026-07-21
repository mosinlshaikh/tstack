"""Local-first Creation OS blueprint for 3D, games, web, and mobile."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


CREATION_BLUEPRINT_SCHEMA = "tstack-creation-blueprint/v1"
CREATION_PLAN_SCHEMA = "tstack-creation-plan/v1"


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


@dataclass(frozen=True)
class CreationStage:
    id: str
    name: str
    objective: str
    tools: tuple[str, ...]
    outputs: tuple[str, ...]
    approval_required: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True)
class CreationPlan:
    schema: str
    project_type: str
    goal: str
    stages: tuple[CreationStage, ...]
    validation: tuple[str, ...]
    approval_required: bool = True
    execution_allowed: bool = False


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


def create_plan(project_type: str, goal: str) -> CreationPlan:
    kind = project_type.strip().lower()
    text = goal.strip()
    if not kind:
        raise ValueError("project type is required")
    if not text:
        raise ValueError("creation goal is required")

    base = [
        CreationStage("CREATE-001", "Discussion", "Clarify requirements, target users, platform, style, constraints, and acceptance criteria.", ("orchestrator-agent", "product-agent"), ("requirements brief", "acceptance criteria")),
        CreationStage("CREATE-002", "Plan", "Create architecture, toolchain, folder structure, task graph, risks, and approval gates.", ("architect-agent", "security-agent"), ("creation plan", "risk register")),
    ]
    specific: list[CreationStage]
    validation: list[str]
    if kind in {"image-to-glb", "3d-character"}:
        specific = [
            CreationStage("CREATE-003", "3D Asset Pipeline", "Analyze image, segment subject, estimate depth, generate mesh, clean topology, UV, texture, and export.", ("blender-bridge", "local-ai-bridge", "ffmpeg-bridge"), ("mesh plan", "texture plan", "GLB export plan")),
            CreationStage("CREATE-004", "3D Validation", "Validate polygon count, texture quality, estimated geometry, mobile optimization, and GLB structure.", ("blender-bridge",), ("validation report", "confidence report")),
        ]
        validation = ("front geometry confidence", "side/back estimation warning", "GLB validation", "mobile optimization check")
    elif kind in {"2d-game", "3d-game"}:
        specific = [
            CreationStage("CREATE-003", "Game Design", "Create game design document, mechanics, scenes, levels, controls, UI, audio, and save-system plan.", ("godot-bridge", "blender-bridge", "asset-library"), ("GDD", "scene plan", "asset plan")),
            CreationStage("CREATE-004", "Game Build and Test", "Plan local Godot project, scripts, tests, profiling, and platform builds.", ("godot-bridge", "android-bridge"), ("playable build plan", "test plan", "export plan")),
        ]
        validation = ("play test", "scene load test", "performance profile", "platform export validation")
    elif kind == "android-app":
        specific = [
            CreationStage("CREATE-003", "Android Build Plan", "Plan Kotlin/Compose or framework project, Gradle setup, UI, APIs, tests, lint, APK/AAB outputs.", ("android-bridge",), ("Android project plan", "test plan", "signing plan")),
            CreationStage("CREATE-004", "Android Validation", "Plan emulator/device install, screenshots, performance, crash checks, lint, and bundle validation.", ("android-bridge",), ("APK validation", "AAB validation", "device test report")),
        ]
        validation = ("gradle test", "gradle lint", "assembleDebug", "bundleRelease approval")
    elif kind == "ios-app":
        specific = [
            CreationStage("CREATE-003", "iOS Project Plan", "Plan Swift/SwiftUI project, tests, static checks, and Mac build-node handoff.", ("xcode-mac-bridge",), ("iOS project plan", "Mac build node plan")),
            CreationStage("CREATE-004", "iOS Validation", "Plan xcodebuild, simulator, signing, archive, and store package verification on Mac.", ("xcode-mac-bridge",), ("simulator report", "archive plan")),
        ]
        validation = ("Mac + Xcode required", "xcodebuild test", "simctl validation", "signing approval")
    else:
        specific = [
            CreationStage("CREATE-003", "Implementation Plan", "Plan project files, UI/UX, backend, database, tests, security, and local preview.", ("website-builder-agent", "developer-agent", "browser-bridge"), ("implementation plan", "preview plan")),
            CreationStage("CREATE-004", "Release Plan", "Plan tests, security checks, deployment package, release notes, and rollback.", ("docker-bridge", "deployment-bridge"), ("release plan", "rollback plan")),
        ]
        validation = ("tests", "security scan", "local preview", "deployment approval")

    final = [
        CreationStage("CREATE-005", "Local Preview", "Prepare local preview or artifact review for human approval.", ("browser-bridge", "desktop-control-agent"), ("preview checklist", "approval packet")),
        CreationStage("CREATE-006", "Deployment Package", "Prepare store-ready files, release notes, deployment plan, and rollback package.", ("deployment-bridge", "github-bridge"), ("deployment package", "release notes", "rollback package")),
    ]
    return CreationPlan(CREATION_PLAN_SCHEMA, kind, text, tuple(base + specific + final), tuple(validation))


def creation_plan_json(plan: CreationPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def creation_plan_markdown(plan: CreationPlan) -> str:
    lines = [
        "# TStack Creation Plan",
        "",
        f"- Project type: `{plan.project_type}`",
        f"- Goal: {plan.goal}",
        f"- Stages: {len(plan.stages)}",
        f"- Approval required: {'yes' if plan.approval_required else 'no'}",
        f"- Execution allowed: {'yes' if plan.execution_allowed else 'no'}",
        "",
        "## Stages",
        "",
    ]
    for stage in plan.stages:
        lines.extend([f"### {stage.id} - {stage.name}", "", stage.objective, "", f"- Tools: {', '.join(stage.tools)}", f"- Outputs: {', '.join(stage.outputs)}", ""])
    lines.extend(["## Validation", ""])
    lines.extend(f"- {item}" for item in plan.validation)
    return "\n".join(lines) + "\n"

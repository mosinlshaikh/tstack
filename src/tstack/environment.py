"""Local creation environment detection and planning."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass


ENVIRONMENT_REPORT_SCHEMA = "tstack-environment-report/v1"


@dataclass(frozen=True)
class ToolCheck:
    id: str
    name: str
    command: str
    detected: bool
    path: str | None
    version: str | None
    profile: str
    install_hint: str


@dataclass(frozen=True)
class EnvironmentReport:
    schema: str
    tools_checked: int
    detected: int
    missing: int
    profile: str
    tools: tuple[ToolCheck, ...]
    approval_required_for_install: bool = True
    execution_allowed: bool = False


TOOLS = (
    ("python", "Python", "python", "core", "Install Python 3.10+ and ensure it is on PATH."),
    ("git", "Git", "git", "core", "Install Git and ensure it is on PATH."),
    ("node", "Node.js", "node", "web", "Install Node.js LTS."),
    ("docker", "Docker", "docker", "devops", "Install Docker Desktop or compatible Docker engine."),
    ("blender", "Blender", "blender", "3d", "Install Blender and add blender executable to PATH."),
    ("godot", "Godot", "godot", "game", "Install Godot and add it to PATH."),
    ("java", "Java/JDK", "java", "mobile", "Install JDK 17+ for Android builds."),
    ("adb", "Android Debug Bridge", "adb", "mobile", "Install Android SDK platform-tools."),
    ("gradle", "Gradle", "gradle", "mobile", "Use Gradle wrapper or install Gradle."),
    ("ffmpeg", "FFmpeg", "ffmpeg", "media", "Install FFmpeg and add it to PATH."),
)


def _version(command: str) -> str | None:
    flags = ("--version", "-version")
    for flag in flags:
        try:
            result = subprocess.run([command, flag], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            continue
        output = (result.stdout or result.stderr).strip().splitlines()
        if output:
            return output[0][:200]
    return None


def inspect_environment(*, profile: str = "all") -> EnvironmentReport:
    if profile not in {"all", "core", "web", "devops", "3d", "game", "mobile", "media"}:
        raise ValueError("unsupported environment profile")
    checks: list[ToolCheck] = []
    for tool_id, name, command, tool_profile, hint in TOOLS:
        if profile != "all" and tool_profile != profile and tool_profile != "core":
            continue
        path = shutil.which(command)
        checks.append(ToolCheck(tool_id, name, command, path is not None, path, _version(command) if path else None, tool_profile, hint))
    detected = sum(1 for item in checks if item.detected)
    return EnvironmentReport(ENVIRONMENT_REPORT_SCHEMA, len(checks), detected, len(checks) - detected, profile, tuple(checks))


def environment_json(report: EnvironmentReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def environment_markdown(report: EnvironmentReport) -> str:
    lines = [
        "# TStack Environment Report",
        "",
        f"- Profile: `{report.profile}`",
        f"- Tools checked: {report.tools_checked}",
        f"- Detected: {report.detected}",
        f"- Missing: {report.missing}",
        f"- Install approval required: {'yes' if report.approval_required_for_install else 'no'}",
        f"- Execution allowed: {'yes' if report.execution_allowed else 'no'}",
        "",
        "## Tools",
        "",
    ]
    for tool in report.tools:
        status = "detected" if tool.detected else "missing"
        detail = tool.version or tool.install_hint
        lines.append(f"- `{tool.id}` [{status}] - {detail}")
    return "\n".join(lines) + "\n"

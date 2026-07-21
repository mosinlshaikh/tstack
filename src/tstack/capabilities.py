"""Capability model registry with honest implementation status."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

CAPABILITY_REGISTRY_SCHEMA = "tstack-capability-registry/v1"
CAPABILITY_STATUSES = ("WORKING", "EXPERIMENTAL", "PLAN-ONLY", "UNSUPPORTED")


@dataclass(frozen=True)
class CapabilityDefinition:
    id: str
    status: str
    risk: str
    approval_required: bool
    rollback_support: str
    platforms: tuple[str, ...]
    timeout_seconds: int
    permission: str
    input_schema: str
    output_schema: str
    audit_behavior: str


CAPABILITIES: tuple[CapabilityDefinition, ...] = (
    CapabilityDefinition("filesystem.read", "WORKING", "low", False, "not-required", ("windows", "linux", "macos"), 30, "read_files", "path", "file metadata/content", "audit optional read event"),
    CapabilityDefinition("filesystem.search", "WORKING", "low", False, "not-required", ("windows", "linux", "macos"), 60, "read_files", "root/query", "matches", "audit optional search event"),
    CapabilityDefinition("filesystem.move", "EXPERIMENTAL", "medium", True, "transaction-manifest", ("windows", "linux", "macos"), 120, "write_files", "source/destination", "move result", "audit required"),
    CapabilityDefinition("filesystem.write", "EXPERIMENTAL", "medium", True, "snapshot", ("windows", "linux", "macos"), 60, "write_files", "target/content", "write result", "audit required"),
    CapabilityDefinition("process.run", "EXPERIMENTAL", "medium", True, "none", ("windows", "linux", "macos"), 60, "run_process", "argv/cwd", "exit/stdout/stderr", "audit required"),
    CapabilityDefinition("project.scan", "WORKING", "low", False, "not-required", ("windows", "linux", "macos"), 120, "read_project", "path", "scan report", "audit optional scan event"),
    CapabilityDefinition("git.read", "PLAN-ONLY", "low", False, "not-required", ("windows", "linux", "macos"), 30, "git_read", "repo", "git metadata", "not implemented"),
    CapabilityDefinition("git.commit", "UNSUPPORTED", "medium", True, "git reset/revert plan required", ("windows", "linux", "macos"), 60, "git_write", "message/files", "commit result", "not implemented"),
    CapabilityDefinition("browser.open", "UNSUPPORTED", "medium", True, "session close", ("windows", "linux", "macos"), 60, "browser_control", "url/profile", "browser session", "not implemented"),
    CapabilityDefinition("browser.navigate", "UNSUPPORTED", "medium", True, "session state", ("windows", "linux", "macos"), 60, "browser_control", "url", "navigation result", "not implemented"),
    CapabilityDefinition("docker.inspect", "PLAN-ONLY", "low", False, "not-required", ("windows", "linux", "macos"), 30, "docker_read", "target", "inspect report", "not implemented"),
    CapabilityDefinition("docker.run", "UNSUPPORTED", "high", True, "container cleanup", ("windows", "linux", "macos"), 300, "docker_run", "image/args", "container result", "not implemented"),
    CapabilityDefinition("ssh.connect", "PLAN-ONLY", "high", True, "not-supported", ("windows", "linux", "macos"), 60, "ssh_plan", "target/command", "ssh plan", "plan-only audit"),
    CapabilityDefinition("blender.inspect", "UNSUPPORTED", "low", False, "not-required", ("windows", "linux", "macos"), 60, "blender_read", "scene", "scene inventory", "not implemented"),
    CapabilityDefinition("blender.execute_task", "UNSUPPORTED", "medium", True, "blender undo", ("windows", "linux", "macos"), 300, "blender_control", "task", "task result", "not implemented"),
    CapabilityDefinition("godot.build", "UNSUPPORTED", "medium", True, "artifact cleanup", ("windows", "linux", "macos"), 600, "game_build", "project/export", "build artifacts", "not implemented"),
    CapabilityDefinition("android.build", "UNSUPPORTED", "medium", True, "artifact cleanup", ("windows", "linux", "macos"), 900, "android_build", "project/variant", "apk/aab", "not implemented"),
    CapabilityDefinition("ios.request_build", "UNSUPPORTED", "high", True, "mac-node cleanup", ("macos",), 1200, "ios_build", "project/signing refs", "archive", "not implemented"),
    CapabilityDefinition("deployment.publish", "UNSUPPORTED", "high", True, "deployment rollback", ("windows", "linux", "macos"), 900, "deploy", "artifact/environment", "deployment result", "not implemented"),
)


def list_capability_definitions(status: str | None = None) -> tuple[CapabilityDefinition, ...]:
    if status is not None:
        normalized = status.upper()
        if normalized not in CAPABILITY_STATUSES:
            raise ValueError("unsupported capability status")
        return tuple(item for item in CAPABILITIES if item.status == normalized)
    return CAPABILITIES


def get_capability_definition(capability_id: str) -> CapabilityDefinition:
    for capability in CAPABILITIES:
        if capability.id == capability_id:
            return capability
    raise ValueError(f"unknown capability: {capability_id}")


def validate_capability_registry() -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for capability in CAPABILITIES:
        if capability.id in seen:
            errors.append(f"{capability.id}: duplicate capability id")
        seen.add(capability.id)
        if capability.status not in CAPABILITY_STATUSES:
            errors.append(f"{capability.id}: invalid status")
        if capability.risk not in {"low", "medium", "high"}:
            errors.append(f"{capability.id}: invalid risk")
        if capability.risk == "high" and not capability.approval_required:
            errors.append(f"{capability.id}: high-risk capability must require approval")
        if capability.status == "WORKING" and capability.audit_behavior == "not implemented":
            errors.append(f"{capability.id}: working capability must define audit behavior")
    return tuple(errors)


def capability_registry_json(capabilities: tuple[CapabilityDefinition, ...]) -> str:
    return json.dumps({"schema": CAPABILITY_REGISTRY_SCHEMA, "capabilities": [asdict(item) for item in capabilities]}, indent=2, sort_keys=True) + "\n"


def capability_registry_markdown(capabilities: tuple[CapabilityDefinition, ...]) -> str:
    lines = ["# TStack Capability Registry", ""]
    for item in capabilities:
        lines.extend([
            f"## `{item.id}`",
            "",
            f"- Status: **{item.status}**",
            f"- Risk: `{item.risk}`",
            f"- Approval required: {'yes' if item.approval_required else 'no'}",
            f"- Rollback support: `{item.rollback_support}`",
            f"- Platforms: {', '.join(item.platforms)}",
            f"- Timeout: {item.timeout_seconds}s",
            f"- Permission: `{item.permission}`",
            "",
        ])
    return "\n".join(lines)


def capability_validation_json(errors: tuple[str, ...]) -> str:
    return json.dumps({"schema": "tstack-capability-validation/v1", "valid": not errors, "errors": list(errors), "capabilities_checked": len(CAPABILITIES)}, indent=2, sort_keys=True) + "\n"

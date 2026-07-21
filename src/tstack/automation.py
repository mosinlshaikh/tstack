"""Automation capability registry for TStack."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Iterable


AUTOMATION_REGISTRY_SCHEMA = "tstack-automation-registry/v1"
AUTOMATION_VALIDATION_SCHEMA = "tstack-automation-validation/v1"


@dataclass(frozen=True)
class AutomationCapability:
    id: str
    name: str
    category: str
    status: str
    mode: str
    command: str | None
    execution_allowed: bool
    approval_required: bool
    trust_required: bool
    description: str
    safety_boundary: str


@dataclass(frozen=True)
class AutomationValidationResult:
    valid: bool
    capabilities_checked: int
    errors: tuple[str, ...]


CAPABILITIES: tuple[AutomationCapability, ...] = (
    AutomationCapability(
        id="ssh-plan",
        name="SSH automation planner",
        category="remote-operations",
        status="available",
        mode="plan-only",
        command="tstack ssh plan",
        execution_allowed=False,
        approval_required=True,
        trust_required=True,
        description="Creates policy-checked SSH command plans without opening a remote connection.",
        safety_boundary="Remote execution is intentionally disabled; a human must review the plan.",
    ),
    AutomationCapability(
        id="project-rule-plugins",
        name="Project declarative rule plugins",
        category="plugins",
        status="available",
        mode="non-executable-rules",
        command="tstack scan",
        execution_allowed=True,
        approval_required=False,
        trust_required=False,
        description="Loads local JSON rules from .tstack/rules for deterministic scan findings.",
        safety_boundary="Rules inspect paths and metadata only; they do not execute project code.",
    ),
    AutomationCapability(
        id="python-rule-plugins",
        name="Installed Python rule plugins",
        category="plugins",
        status="available-with-trust-policy",
        mode="trusted-executable-plugin",
        command="tstack scan",
        execution_allowed=True,
        approval_required=True,
        trust_required=True,
        description="Loads installed tstack.rules entry points after plugin trust checks.",
        safety_boundary="Executable plugins must be reviewed and allowlisted before load.",
    ),
    AutomationCapability(
        id="knowledge-packs",
        name="Engineering knowledge packs",
        category="knowledge",
        status="available",
        mode="read-only",
        command="tstack knowledge",
        execution_allowed=False,
        approval_required=False,
        trust_required=False,
        description="Lists, explains, and validates local engineering knowledge packs.",
        safety_boundary="Knowledge packs are read-only guidance and do not change projects.",
    ),
    AutomationCapability(
        id="release-trust-gate",
        name="Release trust automation",
        category="release",
        status="available",
        mode="verification-only",
        command="tstack release-check",
        execution_allowed=False,
        approval_required=True,
        trust_required=True,
        description="Verifies release integrity, reproducibility, SBOM, and provenance evidence.",
        safety_boundary="Release gates verify artifacts; they do not publish or deploy releases.",
    ),
    AutomationCapability(
        id="auto-plugin-install",
        name="Automatic plugin installation",
        category="plugins",
        status="blocked",
        mode="not-supported",
        command=None,
        execution_allowed=False,
        approval_required=True,
        trust_required=True,
        description="Installing arbitrary plugins from remote sources is not enabled.",
        safety_boundary="Plugin installation must stay explicit and reviewed.",
    ),
)


def list_capabilities() -> tuple[AutomationCapability, ...]:
    return tuple(sorted(CAPABILITIES, key=lambda item: item.id))


def get_capability(capability_id: str) -> AutomationCapability:
    for capability in CAPABILITIES:
        if capability.id == capability_id:
            return capability
    raise KeyError(f"unknown automation capability: {capability_id}")


def validate_automation(capabilities: Iterable[AutomationCapability] | None = None) -> AutomationValidationResult:
    errors: list[str] = []
    seen: set[str] = set()
    checked = 0
    for capability in capabilities or list_capabilities():
        checked += 1
        if not capability.id:
            errors.append("capability id is required")
        if capability.id in seen:
            errors.append(f"{capability.id}: duplicate capability id")
        seen.add(capability.id)
        if capability.status not in {"available", "available-with-trust-policy", "blocked"}:
            errors.append(f"{capability.id}: unsupported status {capability.status!r}")
        if capability.execution_allowed and capability.status == "blocked":
            errors.append(f"{capability.id}: blocked capability cannot allow execution")
        if capability.execution_allowed and capability.trust_required and not capability.approval_required:
            errors.append(f"{capability.id}: trusted executable automation must require approval")
        if not capability.description:
            errors.append(f"{capability.id}: description is required")
        if not capability.safety_boundary:
            errors.append(f"{capability.id}: safety boundary is required")
    return AutomationValidationResult(not errors, checked, tuple(errors))


def registry_json(capabilities: Iterable[AutomationCapability] | None = None) -> str:
    return json.dumps(
        {
            "schema": AUTOMATION_REGISTRY_SCHEMA,
            "capabilities": [asdict(item) for item in (capabilities or list_capabilities())],
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def registry_markdown(capabilities: Iterable[AutomationCapability] | None = None) -> str:
    lines = ["# TStack Automation Registry", ""]
    for capability in capabilities or list_capabilities():
        lines.extend(
            [
                f"## {capability.name}",
                "",
                f"- ID: `{capability.id}`",
                f"- Category: `{capability.category}`",
                f"- Status: `{capability.status}`",
                f"- Mode: `{capability.mode}`",
                f"- Command: `{capability.command or 'not available'}`",
                f"- Execution allowed: `{str(capability.execution_allowed).lower()}`",
                f"- Approval required: `{str(capability.approval_required).lower()}`",
                f"- Trust required: `{str(capability.trust_required).lower()}`",
                f"- Description: {capability.description}",
                f"- Safety boundary: {capability.safety_boundary}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def validation_json(result: AutomationValidationResult) -> str:
    return json.dumps(
        {
            "schema": AUTOMATION_VALIDATION_SCHEMA,
            "valid": result.valid,
            "capabilities_checked": result.capabilities_checked,
            "errors": list(result.errors),
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def validation_markdown(result: AutomationValidationResult) -> str:
    verdict = "PASS" if result.valid else "FAIL"
    lines = [
        "# TStack Automation Validation",
        "",
        f"- Verdict: **{verdict}**",
        f"- Capabilities checked: {result.capabilities_checked}",
    ]
    if result.errors:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines) + "\n"

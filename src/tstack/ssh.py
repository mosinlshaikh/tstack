"""Safe SSH automation planning for TStack.

This module intentionally does not execute remote commands. It creates and
validates policy-controlled plans so remote execution can be added later behind
explicit approval and audit controls.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SSH_POLICY_SCHEMA = "tstack-ssh-policy/v1"
SSH_PLAN_SCHEMA = "tstack-ssh-plan/v1"


@dataclass(frozen=True)
class SshPlan:
    valid: bool
    target: str
    command: str
    user: str | None
    port: int
    approval_required: bool
    execution_allowed: bool
    reasons: tuple[str, ...]


def default_ssh_policy_json() -> str:
    return json.dumps(
        {
            "schema": DEFAULT_SSH_POLICY_SCHEMA,
            "mode": "plan-only",
            "approval_required": True,
            "default_user": None,
            "default_port": 22,
            "allowed_targets": [],
            "allowed_commands": [],
            "blocked_command_patterns": [
                "rm -rf /",
                "mkfs",
                "shutdown",
                "reboot",
                "curl .*\\|\\s*sh",
                "wget .*\\|\\s*sh"
            ],
            "audit": {
                "redact_secrets": True,
                "write_plan_receipts": True
            }
        },
        indent=2,
    ) + "\n"


def load_ssh_policy(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_ssh_policy(policy: dict) -> tuple[str, ...]:
    errors: list[str] = []
    if policy.get("schema") != DEFAULT_SSH_POLICY_SCHEMA:
        errors.append("schema must be tstack-ssh-policy/v1")
    if policy.get("mode") not in {"plan-only", "approved-execution"}:
        errors.append("mode must be plan-only or approved-execution")
    if policy.get("approval_required") is not True:
        errors.append("approval_required must be true")
    if not isinstance(policy.get("allowed_targets"), list):
        errors.append("allowed_targets must be a list")
    if not isinstance(policy.get("allowed_commands"), list):
        errors.append("allowed_commands must be a list")
    if not isinstance(policy.get("blocked_command_patterns"), list):
        errors.append("blocked_command_patterns must be a list")
    port = policy.get("default_port", 22)
    if not isinstance(port, int) or port < 1 or port > 65535:
        errors.append("default_port must be an integer from 1 to 65535")
    return tuple(errors)


def create_ssh_policy(root: Path, *, force: bool = False) -> Path:
    destination = root.expanduser().resolve() / ".tstack" / "ssh-policy.json"
    if destination.exists() and not force:
        raise FileExistsError(f"ssh policy already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(default_ssh_policy_json(), encoding="utf-8")
    return destination


def _matches_any(value: str, patterns: list[str]) -> bool:
    return any(re.fullmatch(pattern, value) or pattern == value for pattern in patterns)


def plan_ssh_command(policy: dict, *, target: str, command: str, user: str | None = None, port: int | None = None) -> SshPlan:
    reasons = list(validate_ssh_policy(policy))
    effective_user = user or policy.get("default_user")
    effective_port = port or int(policy.get("default_port", 22))

    allowed_targets = policy.get("allowed_targets", [])
    if not _matches_any(target, allowed_targets):
        reasons.append(f"target is not allowlisted: {target}")

    allowed_commands = policy.get("allowed_commands", [])
    if not _matches_any(command, allowed_commands):
        reasons.append("command is not allowlisted")

    for pattern in policy.get("blocked_command_patterns", []):
        if re.search(pattern, command):
            reasons.append(f"command matches blocked pattern: {pattern}")

    if effective_port < 1 or effective_port > 65535:
        reasons.append("port must be from 1 to 65535")

    mode = policy.get("mode")
    execution_allowed = False
    if mode == "approved-execution" and not reasons:
        # Future execution still requires a separate explicit approval flag.
        execution_allowed = False
        reasons.append("remote execution is not implemented; plan only")

    return SshPlan(
        valid=not reasons,
        target=target,
        command=command,
        user=effective_user,
        port=effective_port,
        approval_required=True,
        execution_allowed=execution_allowed,
        reasons=tuple(reasons),
    )


def ssh_plan_json(plan: SshPlan) -> str:
    return json.dumps(
        {
            "schema": SSH_PLAN_SCHEMA,
            "valid": plan.valid,
            "target": plan.target,
            "command": plan.command,
            "user": plan.user,
            "port": plan.port,
            "approval_required": plan.approval_required,
            "execution_allowed": plan.execution_allowed,
            "reasons": list(plan.reasons),
        },
        indent=2,
    ) + "\n"


def ssh_plan_markdown(plan: SshPlan) -> str:
    lines = [
        "# TStack SSH Plan",
        "",
        f"- Verdict: **{'PASS' if plan.valid else 'HOLD'}**",
        f"- Target: `{plan.target}`",
        f"- User: `{plan.user or ''}`",
        f"- Port: `{plan.port}`",
        f"- Approval required: `{str(plan.approval_required).lower()}`",
        f"- Execution allowed: `{str(plan.execution_allowed).lower()}`",
        "",
        "## Command",
        "",
        f"```text\n{plan.command}\n```",
    ]
    if plan.reasons:
        lines.extend(["", "## Reasons", ""])
        lines.extend(f"- {reason}" for reason in plan.reasons)
    return "\n".join(lines) + "\n"

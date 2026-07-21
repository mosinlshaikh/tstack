"""Sandbox policy and subprocess planning foundation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SANDBOX_POLICY_SCHEMA = "tstack-sandbox-policy/v1"
SANDBOX_PLAN_SCHEMA = "tstack-sandbox-plan/v1"

DEFAULT_ALLOWED_COMMANDS = ("python", "pytest", "git", "node", "npm")
SENSITIVE_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "KEY", "CREDENTIAL", "AUTH")
SHELL_METACHARS = ("&&", "||", ";", "|", ">", "<", "`", "$(", "\n")


@dataclass(frozen=True)
class SandboxPolicy:
    schema: str
    workspace: str
    allowed_commands: tuple[str, ...]
    network_allowed: bool
    timeout_seconds: int
    allow_shell: bool
    writable: bool


@dataclass(frozen=True)
class SandboxPlan:
    schema: str
    command: tuple[str, ...]
    workspace: str
    network_allowed: bool
    timeout_seconds: int
    writable: bool
    execution_allowed: bool
    blockers: tuple[str, ...]
    redacted_env_markers: tuple[str, ...]


def default_sandbox_policy(workspace: Path) -> SandboxPolicy:
    root = workspace.expanduser().resolve()
    return SandboxPolicy(SANDBOX_POLICY_SCHEMA, str(root), DEFAULT_ALLOWED_COMMANDS, False, 60, False, False)


def sandbox_policy_json(policy: SandboxPolicy) -> str:
    return json.dumps(asdict(policy), indent=2, sort_keys=True) + "\n"


def load_sandbox_policy(path: Path) -> SandboxPolicy:
    payload = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    if payload.get("schema") != SANDBOX_POLICY_SCHEMA:
        raise ValueError("invalid sandbox policy schema")
    timeout = int(payload.get("timeout_seconds", 60))
    if timeout <= 0 or timeout > 3600:
        raise ValueError("sandbox timeout must be between 1 and 3600 seconds")
    allowed = tuple(str(item) for item in payload.get("allowed_commands", ()))
    if not allowed:
        raise ValueError("sandbox policy must allow at least one command")
    return SandboxPolicy(
        SANDBOX_POLICY_SCHEMA,
        str(Path(str(payload["workspace"])).expanduser().resolve()),
        allowed,
        bool(payload.get("network_allowed", False)),
        timeout,
        bool(payload.get("allow_shell", False)),
        bool(payload.get("writable", False)),
    )


def _inside(root: Path, path: Path) -> bool:
    resolved = path.expanduser().resolve()
    return resolved == root or root in resolved.parents


def plan_sandbox_command(policy: SandboxPolicy, command: tuple[str, ...], *, cwd: Path | None = None, write: bool = False, network: bool = False) -> SandboxPlan:
    blockers: list[str] = []
    root = Path(policy.workspace).expanduser().resolve()
    working_dir = cwd.expanduser().resolve() if cwd else root
    if not command:
        blockers.append("command is required")
    executable = command[0] if command else ""
    if executable not in policy.allowed_commands:
        blockers.append(f"command '{executable}' is not allowlisted")
    if not _inside(root, working_dir):
        blockers.append("working directory escapes sandbox workspace")
    if not policy.allow_shell and any(any(marker in part for marker in SHELL_METACHARS) for part in command):
        blockers.append("shell metacharacters are blocked")
    if write and not policy.writable:
        blockers.append("write access is disabled by policy")
    if network and not policy.network_allowed:
        blockers.append("network access is disabled by policy")
    return SandboxPlan(
        SANDBOX_PLAN_SCHEMA,
        command,
        str(working_dir),
        policy.network_allowed and network,
        policy.timeout_seconds,
        policy.writable and write,
        False,
        tuple(blockers),
        SENSITIVE_ENV_MARKERS,
    )


def sandbox_plan_json(plan: SandboxPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def sandbox_plan_markdown(plan: SandboxPlan) -> str:
    lines = [
        "# TStack Sandbox Plan",
        "",
        f"- Command: `{' '.join(plan.command)}`",
        f"- Workspace: `{plan.workspace}`",
        f"- Network allowed: {'yes' if plan.network_allowed else 'no'}",
        f"- Timeout seconds: {plan.timeout_seconds}",
        f"- Writable: {'yes' if plan.writable else 'no'}",
        f"- Execution allowed: {'yes' if plan.execution_allowed else 'no'}",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in plan.blockers or ("executor not implemented",))
    lines.extend(["", "## Environment Redaction", ""])
    lines.extend(f"- `{item}`" for item in plan.redacted_env_markers)
    return "\n".join(lines) + "\n"

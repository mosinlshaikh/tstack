"""Sandbox policy and subprocess planning foundation."""

from __future__ import annotations

import json
import os
import subprocess
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from tstack.runtime import RUNTIME_DECISION_SCHEMA, RUNTIME_REQUEST_SCHEMA

SANDBOX_POLICY_SCHEMA = "tstack-sandbox-policy/v1"
SANDBOX_PLAN_SCHEMA = "tstack-sandbox-plan/v1"
SANDBOX_RESULT_SCHEMA = "tstack-sandbox-result/v1"

DEFAULT_ALLOWED_COMMANDS = ("python", "pytest", "git", "node", "npm")
SENSITIVE_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "KEY", "CREDENTIAL", "AUTH")
SHELL_METACHARS = ("&&", "||", ";", "|", ">", "<", "`", "$(", "\n")
LEGACY_UNSIGNED_OPT_IN = "TSTACK_ALLOW_LEGACY_UNSIGNED_EXECUTION"


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


@dataclass(frozen=True)
class SandboxResult:
    schema: str
    command: tuple[str, ...]
    workspace: str
    executed: bool
    exit_code: int | None
    timed_out: bool
    stdout: str
    stderr: str
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


def _redacted_env() -> dict[str, str]:
    clean: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if any(marker in upper for marker in SENSITIVE_ENV_MARKERS):
            continue
        clean[key] = value
    return clean


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _approval_blockers(request_path: Path | None, decision_path: Path | None) -> tuple[str, ...]:
    if request_path is None or decision_path is None:
        return ("runtime request and decision are required for sandbox execution",)
    try:
        request = json.loads(request_path.expanduser().resolve().read_text(encoding="utf-8"))
        decision = json.loads(decision_path.expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"runtime approval could not be read: {exc}",)
    blockers: list[str] = []
    if request.get("schema") != RUNTIME_REQUEST_SCHEMA:
        blockers.append("invalid runtime request schema")
    if decision.get("schema") != RUNTIME_DECISION_SCHEMA:
        blockers.append("invalid runtime decision schema")
    if request.get("capability") != "process.run":
        blockers.append("runtime request must use process.run capability")
    if decision.get("request_id") != request.get("request_id"):
        blockers.append("runtime request and decision ids do not match")
    if decision.get("request_hash") != request.get("request_hash"):
        blockers.append("runtime decision is not bound to request hash")
    unsigned = {key: request[key] for key in request if key != "request_hash"}
    if _hash_payload(unsigned) != request.get("request_hash"):
        blockers.append("runtime request hash mismatch")
    if decision.get("approved") is not True:
        blockers.append("runtime decision is not approved")
    return tuple(blockers)


def run_sandbox_command(policy: SandboxPolicy, command: tuple[str, ...], *, cwd: Path | None = None, write: bool = False, network: bool = False, request_path: Path | None = None, decision_path: Path | None = None) -> SandboxResult:
    plan = plan_sandbox_command(policy, command, cwd=cwd, write=write, network=network)
    legacy_enabled = os.environ.get(LEGACY_UNSIGNED_OPT_IN, "").strip() == "1"
    compatibility_blockers = () if legacy_enabled else (
        "legacy unsigned sandbox execution is disabled; use tstack-secure sandbox-run",
    )
    blockers = plan.blockers + compatibility_blockers + _approval_blockers(request_path, decision_path)
    if blockers:
        return SandboxResult(SANDBOX_RESULT_SCHEMA, plan.command, plan.workspace, False, None, False, "", "", blockers, plan.redacted_env_markers)
    try:
        completed = subprocess.run(
            list(plan.command),
            cwd=plan.workspace,
            env=_redacted_env(),
            shell=False,
            capture_output=True,
            text=True,
            timeout=plan.timeout_seconds,
        )
        return SandboxResult(
            SANDBOX_RESULT_SCHEMA,
            plan.command,
            plan.workspace,
            True,
            completed.returncode,
            False,
            completed.stdout[-4000:],
            completed.stderr[-4000:],
            (),
            plan.redacted_env_markers,
        )
    except subprocess.TimeoutExpired as exc:
        return SandboxResult(SANDBOX_RESULT_SCHEMA, plan.command, plan.workspace, True, None, True, (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "command timed out", (), plan.redacted_env_markers)
    except OSError as exc:
        return SandboxResult(SANDBOX_RESULT_SCHEMA, plan.command, plan.workspace, False, None, False, "", str(exc), (str(exc),), plan.redacted_env_markers)


def sandbox_result_json(result: SandboxResult) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


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


def sandbox_result_markdown(result: SandboxResult) -> str:
    lines = [
        "# TStack Sandbox Result",
        "",
        f"- Command: `{' '.join(result.command)}`",
        f"- Workspace: `{result.workspace}`",
        f"- Executed: {'yes' if result.executed else 'no'}",
        f"- Exit code: `{result.exit_code}`",
        f"- Timed out: {'yes' if result.timed_out else 'no'}",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers or ("none",))
    lines.extend(["", "## Stdout", "", "```text", result.stdout, "```", "", "## Stderr", "", "```text", result.stderr, "```", ""])
    return "\n".join(lines) + "\n"

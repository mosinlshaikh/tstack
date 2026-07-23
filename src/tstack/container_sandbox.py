"""Rootless Docker sandbox runtime for untrusted TStack workloads.

This module builds and executes deny-by-default container commands. It never
mounts the Docker socket, never requests privileged mode, drops Linux
capabilities, disables networking by default, and confines writable access to
an explicitly supplied workspace.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

SANDBOX_SCHEMA = "tstack-container-sandbox/v1"
NETWORK_MODES = frozenset({"none", "bridge"})


class SandboxUnavailableError(RuntimeError):
    """Raised when a compatible rootless Docker runtime is unavailable."""


class SandboxPolicyError(PermissionError):
    """Raised when a requested sandbox configuration violates policy."""


@dataclass(frozen=True)
class SandboxProfile:
    name: str
    cpu_limit: float
    memory_mb: int
    pids_limit: int
    timeout_seconds: int
    network: str = "none"
    read_only_root: bool = True
    workspace_writable: bool = True
    no_new_privileges: bool = True
    cap_drop_all: bool = True

    def validate(self) -> None:
        if not self.name or self.name != self.name.strip().lower():
            raise ValueError("sandbox profile name must be lowercase")
        if not 0.1 <= self.cpu_limit <= 32:
            raise ValueError("cpu_limit must be between 0.1 and 32")
        if not 64 <= self.memory_mb <= 131072:
            raise ValueError("memory_mb must be between 64 and 131072")
        if not 16 <= self.pids_limit <= 4096:
            raise ValueError("pids_limit must be between 16 and 4096")
        if not 1 <= self.timeout_seconds <= 86400:
            raise ValueError("timeout_seconds must be between 1 and 86400")
        if self.network not in NETWORK_MODES:
            raise ValueError(f"unsupported network mode: {self.network}")


PROFILES: dict[str, SandboxProfile] = {
    "restricted": SandboxProfile("restricted", 1.0, 512, 128, 120),
    "build": SandboxProfile("build", 2.0, 2048, 256, 900),
    "test": SandboxProfile("test", 2.0, 1024, 256, 600),
}


@dataclass(frozen=True)
class SandboxRequest:
    schema: str
    sandbox_id: str
    image: str
    command: tuple[str, ...]
    workspace: str
    profile: SandboxProfile
    environment: dict[str, str]
    artifact_paths: tuple[str, ...]
    request_hash: str


@dataclass(frozen=True)
class SandboxReceipt:
    schema: str
    sandbox_id: str
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    command_digest: str
    artifacts: tuple[str, ...]


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _safe_relative(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SandboxPolicyError(f"artifact path must be workspace-relative: {value}")
    return path.as_posix()


def _safe_image(image: str) -> str:
    value = image.strip()
    if not value or any(ch.isspace() for ch in value):
        raise SandboxPolicyError("container image must be a non-empty token")
    if value.startswith("-"):
        raise SandboxPolicyError("container image cannot begin with '-'")
    return value


def create_sandbox_request(
    *,
    image: str,
    command: Sequence[str],
    workspace: Path,
    profile: SandboxProfile | str = "restricted",
    environment: Mapping[str, str] | None = None,
    artifact_paths: Sequence[str] = (),
    sandbox_id: str | None = None,
) -> SandboxRequest:
    selected = PROFILES[profile] if isinstance(profile, str) else profile
    selected.validate()
    resolved = workspace.expanduser().resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"workspace does not exist: {resolved}")
    if resolved.is_symlink():
        raise SandboxPolicyError("workspace symlinks are not allowed")
    normalized_command = tuple(str(item) for item in command)
    if not normalized_command or any(not item for item in normalized_command):
        raise SandboxPolicyError("command must contain non-empty arguments")
    normalized_env: dict[str, str] = {}
    for key, value in dict(environment or {}).items():
        if not key or not key.replace("_", "").isalnum() or key[0].isdigit():
            raise SandboxPolicyError(f"invalid environment key: {key}")
        if key.upper() in {"DOCKER_HOST", "DOCKER_CONFIG", "SSH_AUTH_SOCK", "AWS_SECRET_ACCESS_KEY"}:
            raise SandboxPolicyError(f"sensitive environment key is forbidden: {key}")
        normalized_env[key] = str(value)
    artifacts = tuple(_safe_relative(item) for item in artifact_paths)
    identifier = sandbox_id or f"SBX-{uuid.uuid4().hex}"
    unsigned = {
        "schema": SANDBOX_SCHEMA,
        "sandbox_id": identifier,
        "image": _safe_image(image),
        "command": list(normalized_command),
        "workspace": str(resolved),
        "profile": asdict(selected),
        "environment": normalized_env,
        "artifact_paths": list(artifacts),
    }
    digest = hashlib.sha256(_canonical(unsigned)).hexdigest()
    return SandboxRequest(
        schema=SANDBOX_SCHEMA,
        sandbox_id=identifier,
        image=unsigned["image"],
        command=normalized_command,
        workspace=str(resolved),
        profile=selected,
        environment=normalized_env,
        artifact_paths=artifacts,
        request_hash=digest,
    )


def docker_command(request: SandboxRequest, *, docker_binary: str = "docker") -> tuple[str, ...]:
    """Return a structured rootless Docker command without invoking a shell."""
    profile = request.profile
    workspace_mode = "rw" if profile.workspace_writable else "ro"
    args: list[str] = [
        docker_binary,
        "run",
        "--rm",
        "--name",
        request.sandbox_id.lower(),
        "--workdir",
        "/workspace",
        "--mount",
        f"type=bind,src={request.workspace},dst=/workspace,{workspace_mode}",
        "--cpus",
        str(profile.cpu_limit),
        "--memory",
        f"{profile.memory_mb}m",
        "--pids-limit",
        str(profile.pids_limit),
        "--network",
        profile.network,
    ]
    if profile.read_only_root:
        args.append("--read-only")
        args.extend(["--tmpfs", "/tmp:rw,noexec,nosuid,size=128m"])
    if profile.no_new_privileges:
        args.extend(["--security-opt", "no-new-privileges:true"])
    if profile.cap_drop_all:
        args.extend(["--cap-drop", "ALL"])
    args.extend(["--user", "65532:65532"])
    for key in sorted(request.environment):
        args.extend(["--env", f"{key}={request.environment[key]}"])
    args.append(request.image)
    args.extend(request.command)
    return tuple(args)


def verify_rootless_docker(*, docker_binary: str = "docker") -> dict[str, Any]:
    binary = shutil.which(docker_binary)
    if binary is None:
        raise SandboxUnavailableError("Docker CLI is not installed")
    completed = subprocess.run(
        [binary, "info", "--format", "{{json .SecurityOptions}}"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        env={"PATH": os.environ.get("PATH", "")},
    )
    if completed.returncode != 0:
        raise SandboxUnavailableError(f"Docker daemon unavailable: {completed.stderr.strip()[:500]}")
    output = completed.stdout.lower()
    if "rootless" not in output:
        raise SandboxUnavailableError("Docker is available but rootless mode was not detected")
    return {"binary": binary, "rootless": True, "security_options": completed.stdout.strip()}


def collect_artifacts(request: SandboxRequest) -> tuple[str, ...]:
    root = Path(request.workspace).resolve()
    collected: list[str] = []
    for relative in request.artifact_paths:
        target = (root / relative).resolve()
        if root not in target.parents and target != root:
            raise SandboxPolicyError(f"artifact escaped workspace: {relative}")
        if target.exists():
            collected.append(relative)
    return tuple(collected)


def execute_sandbox(
    request: SandboxRequest,
    *,
    docker_binary: str = "docker",
    verify_rootless: bool = True,
) -> SandboxReceipt:
    if verify_rootless:
        verify_rootless_docker(docker_binary=docker_binary)
    args = docker_command(request, docker_binary=docker_binary)
    timed_out = False
    try:
        completed = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            timeout=request.profile.timeout_seconds,
            check=False,
            shell=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
        exit_code = completed.returncode
        stdout = completed.stdout[-200000:]
        stderr = completed.stderr[-200000:]
        status = "succeeded" if exit_code == 0 else "failed"
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = (exc.stdout or "")[-200000:] if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "")[-200000:] if isinstance(exc.stderr, str) else ""
        status = "timed_out"
        subprocess.run(
            [docker_binary, "rm", "-f", request.sandbox_id.lower()],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            shell=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
    return SandboxReceipt(
        schema=SANDBOX_SCHEMA,
        sandbox_id=request.sandbox_id,
        status=status,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        command_digest=hashlib.sha256(_canonical({"args": list(args)})).hexdigest(),
        artifacts=collect_artifacts(request),
    )


def request_json(request: SandboxRequest) -> str:
    return json.dumps(asdict(request), indent=2, sort_keys=True) + "\n"


def receipt_json(receipt: SandboxReceipt) -> str:
    return json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n"

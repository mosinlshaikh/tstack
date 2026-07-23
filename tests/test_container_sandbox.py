from pathlib import Path

import pytest

from tstack.container_sandbox import (
    PROFILES,
    SandboxPolicyError,
    create_sandbox_request,
    docker_command,
)


def test_restricted_profile_builds_deny_by_default_command(tmp_path: Path) -> None:
    request = create_sandbox_request(
        image="python:3.12-slim",
        command=("python", "-c", "print('ok')"),
        workspace=tmp_path,
        profile="restricted",
        artifact_paths=("report.xml",),
        sandbox_id="SBX-TEST",
    )
    command = docker_command(request)
    joined = " ".join(command)
    assert "--network none" in joined
    assert "--read-only" in command
    assert "--cap-drop ALL" in joined
    assert "no-new-privileges:true" in command
    assert "--pids-limit" in command
    assert "--memory 512m" in joined
    assert "--cpus 1.0" in joined
    assert "/var/run/docker.sock" not in joined
    assert "--privileged" not in command


def test_workspace_must_exist(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        create_sandbox_request(image="alpine:3.20", command=("true",), workspace=tmp_path / "missing")


def test_artifact_escape_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SandboxPolicyError):
        create_sandbox_request(
            image="alpine:3.20",
            command=("true",),
            workspace=tmp_path,
            artifact_paths=("../secret",),
        )


def test_sensitive_environment_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SandboxPolicyError):
        create_sandbox_request(
            image="alpine:3.20",
            command=("true",),
            workspace=tmp_path,
            environment={"SSH_AUTH_SOCK": "/tmp/agent"},
        )


def test_request_hash_changes_with_command(tmp_path: Path) -> None:
    first = create_sandbox_request(image="alpine:3.20", command=("echo", "one"), workspace=tmp_path)
    second = create_sandbox_request(image="alpine:3.20", command=("echo", "two"), workspace=tmp_path)
    assert first.request_hash != second.request_hash


def test_profiles_validate() -> None:
    for profile in PROFILES.values():
        profile.validate()

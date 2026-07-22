from datetime import datetime, timedelta, timezone

import pytest

from tstack.runtime_auth import (
    create_action_request,
    generate_signing_keypair,
    sign_action_request,
    verify_signed_approval,
)


def test_signed_approval_is_bound_to_exact_parameters() -> None:
    private_key, public_key, key_id = generate_signing_keypair()
    request = create_action_request(
        "process.run",
        "Run tests",
        {"executable": "python", "arguments": ["-m", "pytest"], "cwd": ".", "network": False},
        workspace_id="workspace-1",
        request_id="REQ-1",
        nonce="nonce-1",
    )
    approval = sign_action_request(
        request,
        private_key,
        approver="Mosin",
        key_id=key_id,
        reason="Reviewed exact command.",
    )
    checked = verify_signed_approval(request, approval, public_key)
    assert checked.request_id == request.request_id
    assert checked.parameters_hash == request.parameters_hash


def test_modified_parameters_invalidate_request() -> None:
    private_key, public_key, key_id = generate_signing_keypair()
    request = create_action_request(
        "process.run",
        "Run tests",
        {"executable": "python", "arguments": ["-m", "pytest"]},
        workspace_id="workspace-1",
        request_id="REQ-2",
        nonce="nonce-2",
    )
    approval = sign_action_request(request, private_key, approver="Mosin", key_id=key_id, reason="Reviewed.")
    tampered = dict(request.__dict__)
    tampered["parameters"] = {"executable": "python", "arguments": ["cleanup.py"]}
    with pytest.raises(ValueError, match="action request hash mismatch|action parameter hash mismatch"):
        verify_signed_approval(tampered, approval, public_key)


def test_expired_approval_is_rejected() -> None:
    private_key, public_key, key_id = generate_signing_keypair()
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    request = create_action_request(
        "filesystem.move_batch",
        "Organize files",
        {"plan_hash": "abc", "moves": []},
        workspace_id="workspace-1",
        request_id="REQ-3",
        nonce="nonce-3",
        created_at=issued,
    )
    approval = sign_action_request(
        request,
        private_key,
        approver="Mosin",
        key_id=key_id,
        reason="Reviewed.",
        ttl_seconds=60,
        issued_at=issued,
    )
    with pytest.raises(ValueError, match="expired"):
        verify_signed_approval(request, approval, public_key, now=issued + timedelta(seconds=61))


def test_wrong_public_key_is_rejected() -> None:
    private_key, _, key_id = generate_signing_keypair()
    _, wrong_public_key, _ = generate_signing_keypair()
    request = create_action_request(
        "process.run",
        "Run tests",
        {"executable": "python", "arguments": ["-m", "pytest"]},
        workspace_id="workspace-1",
        request_id="REQ-4",
        nonce="nonce-4",
    )
    approval = sign_action_request(request, private_key, approver="Mosin", key_id=key_id, reason="Reviewed.")
    with pytest.raises(ValueError, match="signature"):
        verify_signed_approval(request, approval, wrong_public_key)

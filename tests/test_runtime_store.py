from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from tstack.runtime_auth import create_action_request, generate_signing_keypair, sign_action_request
from tstack.runtime_store import ApprovalAlreadyConsumedError, approval_status, consume_approval, register_approval


def _registered_approval(tmp_path):
    private_key, _, key_id = generate_signing_keypair()
    issued = datetime.now(timezone.utc).replace(microsecond=0)
    request = create_action_request(
        "project.scan",
        "Scan the approved workspace",
        {"root": ".", "mode": "read-only"},
        workspace_id="workspace-1",
        request_id="REQ-STORE-1",
        nonce="nonce-store-1",
        created_at=issued,
    )
    approval = sign_action_request(
        request,
        private_key,
        approver="Mosin",
        key_id=key_id,
        reason="Reviewed exact scan parameters.",
        ttl_seconds=300,
        issued_at=issued,
    )
    database = tmp_path / "runtime.db"
    register_approval(database, request, approval)
    return database, request


def test_approval_can_be_consumed_once(tmp_path) -> None:
    database, request = _registered_approval(tmp_path)
    consume_approval(
        database,
        request_id=request.request_id,
        request_hash=request.request_hash,
        parameters_hash=request.parameters_hash,
        nonce=request.nonce,
        execution_id="EXEC-1",
    )
    status = approval_status(database, request.request_id)
    assert status["consumed"] is True
    assert status["execution_id"] == "EXEC-1"

    with pytest.raises(ApprovalAlreadyConsumedError):
        consume_approval(
            database,
            request_id=request.request_id,
            request_hash=request.request_hash,
            parameters_hash=request.parameters_hash,
            nonce=request.nonce,
            execution_id="EXEC-2",
        )


def test_parameter_hash_mismatch_is_rejected(tmp_path) -> None:
    database, request = _registered_approval(tmp_path)
    with pytest.raises(ValueError, match="parameter hash"):
        consume_approval(
            database,
            request_id=request.request_id,
            request_hash=request.request_hash,
            parameters_hash="0" * 64,
            nonce=request.nonce,
            execution_id="EXEC-BAD",
        )


def test_expired_stored_approval_is_rejected(tmp_path) -> None:
    private_key, _, key_id = generate_signing_keypair()
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    request = create_action_request(
        "project.scan",
        "Scan the approved workspace",
        {"root": ".", "mode": "read-only"},
        workspace_id="workspace-1",
        request_id="REQ-EXPIRED",
        nonce="nonce-expired",
        created_at=issued,
    )
    approval = sign_action_request(
        request,
        private_key,
        approver="Mosin",
        key_id=key_id,
        reason="Reviewed.",
        ttl_seconds=1,
        issued_at=issued,
    )
    database = tmp_path / "runtime.db"
    register_approval(database, request, approval)
    with pytest.raises(ValueError, match="expired"):
        consume_approval(
            database,
            request_id=request.request_id,
            request_hash=request.request_hash,
            parameters_hash=request.parameters_hash,
            nonce=request.nonce,
            execution_id="EXEC-EXPIRED",
            consumed_at=issued + timedelta(seconds=2),
        )


def test_concurrent_consumers_allow_exactly_one_winner(tmp_path) -> None:
    database, request = _registered_approval(tmp_path)

    def consume(index: int) -> str:
        try:
            consume_approval(
                database,
                request_id=request.request_id,
                request_hash=request.request_hash,
                parameters_hash=request.parameters_hash,
                nonce=request.nonce,
                execution_id=f"EXEC-CONCURRENT-{index}",
            )
            return "consumed"
        except ApprovalAlreadyConsumedError:
            return "replayed"

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(consume, range(8)))

    assert results.count("consumed") == 1
    assert results.count("replayed") == 7

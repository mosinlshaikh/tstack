import json

import pytest

from tstack.file_recovery import inspect_recovery_journal
from tstack.runtime_auth import action_json, create_action_request, generate_signing_keypair, sign_action_request
from tstack.runtime_store import ApprovalAlreadyConsumedError, register_approval
from tstack.sandbox import default_sandbox_policy, plan_sandbox_command
from tstack.secure_execution import execute_signed_file_plan, execute_signed_sandbox


def _signed(tmp_path, capability, parameters):
    private, public, key_id = generate_signing_keypair()
    request = create_action_request(capability, "Approved test action", parameters, workspace_id=str(tmp_path))
    approval = sign_action_request(request, private, approver="Mosin", key_id=key_id, reason="Reviewed exact parameters")
    request_path = tmp_path / f"{request.request_id}-request.json"
    approval_path = tmp_path / f"{request.request_id}-approval.json"
    store = tmp_path / "runtime.db"
    request_path.write_text(action_json(request), encoding="utf-8")
    approval_path.write_text(action_json(approval), encoding="utf-8")
    register_approval(store, request, approval)
    return request_path, approval_path, public, store


def test_signed_sandbox_executes_exact_command_once(tmp_path):
    policy = default_sandbox_policy(tmp_path)
    command = ("python", "-c", "print('ok')")
    plan = plan_sandbox_command(policy, command)
    parameters = {
        "command": list(plan.command),
        "cwd": plan.workspace,
        "timeout_seconds": plan.timeout_seconds,
        "write": plan.writable,
        "network": plan.network_allowed,
    }
    request_path, approval_path, public, store = _signed(tmp_path, "process.run", parameters)
    receipt = execute_signed_sandbox(policy, command, request_path=request_path, approval_path=approval_path, public_key_raw=public, store_path=store)
    assert receipt.status == "succeeded"
    assert receipt.result["executed"] is True
    assert "ok" in receipt.result["stdout"]
    with pytest.raises(ApprovalAlreadyConsumedError):
        execute_signed_sandbox(policy, command, request_path=request_path, approval_path=approval_path, public_key_raw=public, store_path=store)


def test_signed_sandbox_rejects_parameter_change(tmp_path):
    policy = default_sandbox_policy(tmp_path)
    approved = ("python", "-c", "print('approved')")
    plan = plan_sandbox_command(policy, approved)
    parameters = {
        "command": list(plan.command), "cwd": plan.workspace,
        "timeout_seconds": plan.timeout_seconds, "write": False, "network": False,
    }
    request_path, approval_path, public, store = _signed(tmp_path, "process.run", parameters)
    with pytest.raises(ValueError, match="exact execution parameters"):
        execute_signed_sandbox(policy, ("python", "-c", "print('changed')"), request_path=request_path, approval_path=approval_path, public_key_raw=public, store_path=store)


def test_signed_file_plan_moves_and_records_recovery_lifecycle(tmp_path):
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    plan = {
        "schema": "tstack-file-organize-plan/v1",
        "root": str(tmp_path),
        "moves": [{"source": "a.txt", "destination": "docs/a.txt"}],
        "conflicts": 0,
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    parameters = {"plan": plan, "dry_run": False, "root": str(tmp_path.resolve())}
    request_path, approval_path, public, store = _signed(tmp_path, "filesystem.move", parameters)
    recovery = tmp_path / "recovery.jsonl"
    receipt = execute_signed_file_plan(
        plan_path,
        request_path=request_path,
        approval_path=approval_path,
        public_key_raw=public,
        store_path=store,
        dry_run=False,
        recovery_journal=recovery,
    )
    assert receipt.status == "succeeded"
    assert not (tmp_path / "a.txt").exists()
    assert (tmp_path / "docs/a.txt").read_text(encoding="utf-8") == "hello"
    report = inspect_recovery_journal(recovery)
    assert report.valid is True
    assert report.terminal is True
    assert report.latest_state == "COMMITTED"
    assert report.moved_pairs == (("a.txt", "docs/a.txt"),)


def test_signed_file_plan_rejects_modified_plan(tmp_path):
    plan = {"schema": "tstack-file-organize-plan/v1", "root": str(tmp_path), "moves": [], "conflicts": 0}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    parameters = {"plan": plan, "dry_run": True, "root": str(tmp_path.resolve())}
    request_path, approval_path, public, store = _signed(tmp_path, "filesystem.move", parameters)
    plan["moves"] = [{"source": "x", "destination": "y"}]
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="exact execution parameters"):
        execute_signed_file_plan(plan_path, request_path=request_path, approval_path=approval_path, public_key_raw=public, store_path=store)

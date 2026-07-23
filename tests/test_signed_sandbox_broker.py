import json

import pytest

from tstack.container_sandbox import SandboxReceipt
from tstack.execution_journal import verify_execution_journal
from tstack.runtime_auth import action_json, create_action_request, generate_signing_keypair, sign_action_request
from tstack.runtime_store import ApprovalAlreadyConsumedError, register_approval
from tstack.signed_sandbox_broker import (
    create_workflow_sandbox_request,
    execute_signed_sandbox_workflow,
    sandbox_parameters,
)
from tstack.task_runtime import submit_task


def _fixture(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sandbox = create_workflow_sandbox_request(
        image="python:3.12-alpine",
        command=("python", "-c", "print('secure')"),
        workspace=workspace,
        profile="restricted",
        artifact_paths=("result.txt",),
    )
    parameters = sandbox_parameters(sandbox)
    task = submit_task(
        tmp_path / "tasks.db",
        workspace_id=str(workspace),
        capability="docker.run",
        intent="Run approved isolated test",
        parameters=parameters,
        task_id="TASK-SANDBOX",
    )
    private, public, key_id = generate_signing_keypair()
    request = create_action_request(
        "docker.run",
        task.intent,
        parameters,
        workspace_id=task.workspace_id,
    )
    approval = sign_action_request(
        request,
        private,
        approver="Mosin",
        key_id=key_id,
        reason="Reviewed exact image, command, profile, workspace and artifacts",
    )
    request_path = tmp_path / "request.json"
    approval_path = tmp_path / "approval.json"
    request_path.write_text(action_json(request), encoding="utf-8")
    approval_path.write_text(action_json(approval), encoding="utf-8")
    approval_store = tmp_path / "approvals.db"
    register_approval(approval_store, request, approval)
    return task, sandbox, request_path, approval_path, public, approval_store


def test_end_to_end_signed_broker_sandbox_workflow(tmp_path):
    task, sandbox, request_path, approval_path, public, approval_store = _fixture(tmp_path)
    journal = tmp_path / "audit.jsonl"

    def fake_executor(request):
        assert request == sandbox
        return SandboxReceipt(
            schema=request.schema,
            sandbox_id=request.sandbox_id,
            status="succeeded",
            exit_code=0,
            stdout="secure\n",
            stderr="",
            timed_out=False,
            command_digest="a" * 64,
            artifacts=(),
        )

    receipt = execute_signed_sandbox_workflow(
        task,
        sandbox=sandbox,
        request_path=request_path,
        approval_path=approval_path,
        public_key_raw=public,
        approval_store=approval_store,
        audit_journal=journal,
        executor=fake_executor,
    )
    assert receipt.capability == "docker.run"
    assert receipt.sandbox.status == "succeeded"
    assert receipt.broker.decision.allowed is True
    valid, errors = verify_execution_journal(journal)
    assert valid is True
    assert errors == ()
    entries = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    assert [entry["state"] for entry in entries] == ["started", "completed"]


def test_replay_is_rejected_before_second_sandbox_execution(tmp_path):
    task, sandbox, request_path, approval_path, public, approval_store = _fixture(tmp_path)
    calls = []

    def fake_executor(request):
        calls.append(request.sandbox_id)
        return SandboxReceipt(request.schema, request.sandbox_id, "succeeded", 0, "", "", False, "b" * 64, ())

    kwargs = dict(
        sandbox=sandbox,
        request_path=request_path,
        approval_path=approval_path,
        public_key_raw=public,
        approval_store=approval_store,
        audit_journal=tmp_path / "audit.jsonl",
        executor=fake_executor,
    )
    execute_signed_sandbox_workflow(task, **kwargs)
    with pytest.raises(ApprovalAlreadyConsumedError):
        execute_signed_sandbox_workflow(task, **kwargs)
    assert calls == [sandbox.sandbox_id]


def test_modified_task_parameters_are_denied(tmp_path):
    task, sandbox, request_path, approval_path, public, approval_store = _fixture(tmp_path)
    modified = submit_task(
        tmp_path / "modified.db",
        workspace_id=task.workspace_id,
        capability="docker.run",
        intent=task.intent,
        parameters={**task.parameters, "sandbox_request_hash": "0" * 64},
        task_id="TASK-MODIFIED",
    )
    with pytest.raises(ValueError, match="task parameters"):
        execute_signed_sandbox_workflow(
            modified,
            sandbox=sandbox,
            request_path=request_path,
            approval_path=approval_path,
            public_key_raw=public,
            approval_store=approval_store,
            audit_journal=tmp_path / "audit.jsonl",
            executor=lambda request: None,
        )


def test_modified_sandbox_command_breaks_exact_binding(tmp_path):
    task, sandbox, request_path, approval_path, public, approval_store = _fixture(tmp_path)
    changed = create_workflow_sandbox_request(
        image=sandbox.image,
        command=("python", "-c", "print('changed')"),
        workspace=tmp_path / "workspace",
        profile="restricted",
        artifact_paths=("result.txt",),
    )
    with pytest.raises(ValueError, match="sandbox request"):
        execute_signed_sandbox_workflow(
            task,
            sandbox=changed,
            request_path=request_path,
            approval_path=approval_path,
            public_key_raw=public,
            approval_store=approval_store,
            audit_journal=tmp_path / "audit.jsonl",
            executor=lambda request: None,
        )

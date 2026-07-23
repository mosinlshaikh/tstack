"""Signed Capability Broker adapter for rootless container execution.

This module connects four previously separate boundaries:

1. a persistent logical task,
2. the deny-by-default capability broker,
3. an exact Ed25519-signed single-use approval, and
4. the rootless Docker sandbox runtime.

The approval is consumed before Docker is invoked.  The action parameters bind
the complete sandbox request, including image, command, workspace, profile,
environment, artifact paths, and sandbox request hash.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from tstack.capability_broker import (
    BROKER_SCHEMA,
    BrokerReceipt,
    CapabilityBroker,
    CapabilityDefinition,
)
from tstack.container_sandbox import (
    SandboxReceipt,
    SandboxRequest,
    create_sandbox_request,
    execute_sandbox,
)
from tstack.execution_journal import append_execution_event
from tstack.runtime_auth import ActionRequest, SignedApproval, verify_signed_approval
from tstack.runtime_store import consume_approval
from tstack.task_runtime import TaskRecord

SIGNED_SANDBOX_WORKFLOW_SCHEMA = "tstack-signed-sandbox-workflow/v1"
SandboxExecutor = Callable[[SandboxRequest], SandboxReceipt]


@dataclass(frozen=True)
class SignedSandboxWorkflowReceipt:
    schema: str
    execution_id: str
    task_id: str
    request_id: str
    capability: str
    broker: BrokerReceipt
    sandbox: SandboxReceipt


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def sandbox_parameters(request: SandboxRequest) -> dict[str, Any]:
    """Return the exact canonical parameters that must be approved."""
    return {
        "sandbox": asdict(request),
        "sandbox_request_hash": request.request_hash,
    }


def _validate_task_binding(task: TaskRecord, request: ActionRequest, sandbox: SandboxRequest) -> None:
    if task.capability != "docker.run":
        raise ValueError("signed sandbox workflow requires docker.run task capability")
    if request.capability != task.capability:
        raise ValueError("task capability does not match signed request capability")
    if request.workspace_id != task.workspace_id:
        raise ValueError("task workspace does not match signed request workspace")
    expected = sandbox_parameters(sandbox)
    if task.parameters != expected:
        raise ValueError("task parameters do not match exact sandbox request")
    if request.parameters != expected:
        raise ValueError("signed request does not match exact sandbox request")


def build_signed_sandbox_broker(
    *,
    task: TaskRecord,
    sandbox: SandboxRequest,
    request_path: Path,
    approval_path: Path,
    public_key_raw: bytes,
    approval_store: Path,
    audit_journal: Path,
    executor: SandboxExecutor = execute_sandbox,
) -> CapabilityBroker:
    """Build a single-purpose broker whose docker.run adapter is fully bound.

    The returned broker allows only the exact supplied task.  Reusing it with a
    different task, workspace, command, image, profile, or request is rejected.
    """
    request_payload = _load(request_path)
    approval_payload = _load(approval_path)
    approval = verify_signed_approval(request_payload, approval_payload, public_key_raw)
    request = ActionRequest(**request_payload)
    _validate_task_binding(task, request, sandbox)

    def policy(candidate: TaskRecord, definition: CapabilityDefinition) -> tuple[bool, str]:
        if definition.name != "docker.run":
            return False, "signed sandbox broker only authorizes docker.run"
        if candidate.task_id != task.task_id:
            return False, "task identity mismatch"
        try:
            _validate_task_binding(candidate, request, sandbox)
        except ValueError as exc:
            return False, str(exc)
        return True, "exact signed single-use sandbox request verified"

    def handler(candidate: TaskRecord) -> Mapping[str, Any]:
        _validate_task_binding(candidate, request, sandbox)
        execution_id = f"EXEC-{uuid.uuid4().hex}"
        consume_approval(
            approval_store,
            request_id=request.request_id,
            request_hash=request.request_hash,
            parameters_hash=request.parameters_hash,
            nonce=request.nonce,
            execution_id=execution_id,
        )
        append_execution_event(
            audit_journal,
            execution_id=execution_id,
            request_id=request.request_id,
            capability="docker.run",
            state="started",
            details={
                "task_id": candidate.task_id,
                "sandbox_id": sandbox.sandbox_id,
                "sandbox_request_hash": sandbox.request_hash,
                "approval_key_id": approval.key_id,
            },
        )
        try:
            receipt = executor(sandbox)
        except Exception as exc:
            append_execution_event(
                audit_journal,
                execution_id=execution_id,
                request_id=request.request_id,
                capability="docker.run",
                state="failed",
                details={"error_type": type(exc).__name__, "error": str(exc)[:1000]},
            )
            raise
        append_execution_event(
            audit_journal,
            execution_id=execution_id,
            request_id=request.request_id,
            capability="docker.run",
            state="completed",
            details={"task_id": candidate.task_id, "status": receipt.status},
            result=asdict(receipt),
        )
        return {
            "execution_id": execution_id,
            "request_id": request.request_id,
            "sandbox": asdict(receipt),
        }

    broker = CapabilityBroker(policy=policy)
    broker.register(
        CapabilityDefinition(
            name="docker.run",
            risk="high",
            approval_required=True,
            sandbox_required=True,
            rollback_supported=False,
            stable=False,
            description="Execute one exact approved request in rootless Docker",
        ),
        handler,
    )
    return broker


def execute_signed_sandbox_workflow(
    task: TaskRecord,
    *,
    sandbox: SandboxRequest,
    request_path: Path,
    approval_path: Path,
    public_key_raw: bytes,
    approval_store: Path,
    audit_journal: Path,
    executor: SandboxExecutor = execute_sandbox,
) -> SignedSandboxWorkflowReceipt:
    """Execute one end-to-end task → broker → approval → sandbox workflow."""
    broker = build_signed_sandbox_broker(
        task=task,
        sandbox=sandbox,
        request_path=request_path,
        approval_path=approval_path,
        public_key_raw=public_key_raw,
        approval_store=approval_store,
        audit_journal=audit_journal,
        executor=executor,
    )
    broker_receipt = broker.dispatch(task)
    result = broker_receipt.result
    sandbox_receipt = SandboxReceipt(**result["sandbox"])
    return SignedSandboxWorkflowReceipt(
        schema=SIGNED_SANDBOX_WORKFLOW_SCHEMA,
        execution_id=str(result["execution_id"]),
        task_id=task.task_id,
        request_id=str(result["request_id"]),
        capability=task.capability,
        broker=broker_receipt,
        sandbox=sandbox_receipt,
    )


def create_workflow_sandbox_request(
    *,
    image: str,
    command: tuple[str, ...],
    workspace: Path,
    profile: str = "restricted",
    environment: Mapping[str, str] | None = None,
    artifact_paths: tuple[str, ...] = (),
) -> SandboxRequest:
    """Convenience wrapper retained as the canonical workflow request builder."""
    return create_sandbox_request(
        image=image,
        command=command,
        workspace=workspace,
        profile=profile,
        environment=environment,
        artifact_paths=artifact_paths,
    )

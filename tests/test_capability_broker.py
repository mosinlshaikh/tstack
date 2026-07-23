from datetime import datetime, timezone

import pytest

from tstack.capability_broker import (
    CapabilityBroker,
    CapabilityDefinition,
    CapabilityDeniedError,
    CapabilityHandlerMissingError,
    UnknownCapabilityError,
    bootstrap_broker,
)
from tstack.task_runtime import TaskRecord


def _task(capability: str, parameters=None) -> TaskRecord:
    now = datetime(2026, 7, 23, 3, 0, tzinfo=timezone.utc).isoformat()
    return TaskRecord(
        schema="tstack-task/v1",
        task_id="TASK-1",
        workspace_id="workspace-1",
        capability=capability,
        intent="test",
        parameters=parameters or {},
        state="RUNNING",
        priority=0,
        max_attempts=1,
        attempt_count=1,
        created_at=now,
        updated_at=now,
        queued_at=now,
        started_at=now,
        completed_at=None,
        lease_owner="worker",
        lease_expires_at=now,
        cancellation_requested_at=None,
        last_error=None,
        result=None,
    )


def test_bootstrap_broker_executes_internal_noop() -> None:
    receipt = bootstrap_broker().dispatch(_task("runtime.noop", {"probe": True}))
    assert receipt.decision.allowed is True
    assert receipt.decision.risk == "none"
    assert receipt.result == {"acknowledged": True, "parameters": {"probe": True}}


def test_unknown_capability_is_denied() -> None:
    with pytest.raises(UnknownCapabilityError):
        bootstrap_broker().dispatch(_task("system.unregistered"))


def test_operational_capability_is_denied_by_default() -> None:
    with pytest.raises(CapabilityDeniedError, match="explicit secure policy"):
        bootstrap_broker().dispatch(_task("process.run", {"command": ["python", "-V"]}))


def test_allowed_capability_without_handler_fails_closed() -> None:
    broker = CapabilityBroker(policy=lambda _task, _definition: (True, "test allow"))
    broker.register(CapabilityDefinition("custom.read", "low", False, False, False))
    with pytest.raises(CapabilityHandlerMissingError):
        broker.dispatch(_task("custom.read"))


def test_high_risk_definition_requires_approval() -> None:
    broker = CapabilityBroker()
    with pytest.raises(ValueError, match="require approval"):
        broker.register(CapabilityDefinition("process.run", "high", False, True, False))


def test_decision_binds_exact_parameters() -> None:
    broker = bootstrap_broker()
    first = broker.decision_for(_task("runtime.noop", {"value": 1}))
    second = broker.decision_for(_task("runtime.noop", {"value": 2}))
    assert first.parameters_hash != second.parameters_hash

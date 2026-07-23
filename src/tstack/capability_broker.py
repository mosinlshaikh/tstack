"""Deny-by-default capability broker for TStack runtime tasks.

The broker is the only component allowed to dispatch a logical task to a
capability handler. It validates a versioned capability definition, evaluates
policy, records a structured decision, and invokes only a registered handler.
Operational handlers remain responsible for exact signed authorization and
sandbox execution; the broker never grants OS access by itself.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from tstack.task_runtime import TaskRecord

BROKER_SCHEMA = "tstack-capability-broker/v1"
DECISION_SCHEMA = "tstack-capability-decision/v1"

RISK_LEVELS = frozenset({"none", "low", "medium", "high", "critical"})
Handler = Callable[[TaskRecord], Mapping[str, Any] | None]
PolicyEvaluator = Callable[[TaskRecord, "CapabilityDefinition"], tuple[bool, str]]


class UnknownCapabilityError(PermissionError):
    """Raised when no capability definition is registered."""


class CapabilityDeniedError(PermissionError):
    """Raised when policy denies a registered capability."""


class CapabilityHandlerMissingError(RuntimeError):
    """Raised when policy allows a capability without an execution handler."""


@dataclass(frozen=True)
class CapabilityDefinition:
    name: str
    risk: str
    approval_required: bool
    sandbox_required: bool
    rollback_supported: bool
    stable: bool = False
    description: str = ""

    def validate(self) -> None:
        if not self.name or self.name != self.name.strip().lower():
            raise ValueError("capability names must be non-empty lowercase identifiers")
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"unsupported capability risk: {self.risk}")
        if self.risk in {"high", "critical"} and not self.approval_required:
            raise ValueError("high and critical capabilities require approval")


@dataclass(frozen=True)
class CapabilityDecision:
    schema: str
    broker_schema: str
    task_id: str
    workspace_id: str
    capability: str
    allowed: bool
    reason: str
    risk: str
    approval_required: bool
    sandbox_required: bool
    rollback_supported: bool
    parameters_hash: str
    decided_at: str


@dataclass(frozen=True)
class BrokerReceipt:
    schema: str
    decision: CapabilityDecision
    result: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parameters_hash(parameters: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(parameters), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def default_policy(task: TaskRecord, definition: CapabilityDefinition) -> tuple[bool, str]:
    """Safe bootstrap policy.

    Only internal, no-risk capabilities are pre-authorized. Every operational
    capability must use a dedicated policy that verifies signed authorization
    and, where required, a sandbox plan before returning allow.
    """
    if definition.risk == "none" and not definition.approval_required and not definition.sandbox_required:
        return True, "internal no-risk capability"
    return False, "operational capability requires an explicit secure policy adapter"


class CapabilityBroker:
    """Versioned capability registry and deny-by-default dispatcher."""

    def __init__(self, *, policy: PolicyEvaluator = default_policy) -> None:
        self._policy = policy
        self._definitions: dict[str, CapabilityDefinition] = {}
        self._handlers: dict[str, Handler] = {}

    def register(self, definition: CapabilityDefinition, handler: Handler | None = None) -> None:
        definition.validate()
        if definition.name in self._definitions:
            raise ValueError(f"capability already registered: {definition.name}")
        self._definitions[definition.name] = definition
        if handler is not None:
            self._handlers[definition.name] = handler

    def definitions(self) -> tuple[CapabilityDefinition, ...]:
        return tuple(self._definitions[name] for name in sorted(self._definitions))

    def decision_for(self, task: TaskRecord) -> CapabilityDecision:
        definition = self._definitions.get(task.capability)
        if definition is None:
            raise UnknownCapabilityError(f"unknown capability: {task.capability}")
        allowed, reason = self._policy(task, definition)
        return CapabilityDecision(
            schema=DECISION_SCHEMA,
            broker_schema=BROKER_SCHEMA,
            task_id=task.task_id,
            workspace_id=task.workspace_id,
            capability=task.capability,
            allowed=bool(allowed),
            reason=str(reason)[:2000],
            risk=definition.risk,
            approval_required=definition.approval_required,
            sandbox_required=definition.sandbox_required,
            rollback_supported=definition.rollback_supported,
            parameters_hash=_parameters_hash(task.parameters),
            decided_at=_utc_now(),
        )

    def dispatch(self, task: TaskRecord) -> BrokerReceipt:
        decision = self.decision_for(task)
        if not decision.allowed:
            raise CapabilityDeniedError(f"capability {task.capability!r} denied: {decision.reason}")
        handler = self._handlers.get(task.capability)
        if handler is None:
            raise CapabilityHandlerMissingError(f"no handler registered for capability: {task.capability}")
        result = dict(handler(task) or {})
        return BrokerReceipt(schema=BROKER_SCHEMA, decision=decision, result=result)


def bootstrap_broker() -> CapabilityBroker:
    """Build the daemon's minimal safe broker registry.

    Operational capabilities are registered for discovery and policy reporting
    but intentionally have no handlers and remain denied by default.
    """
    broker = CapabilityBroker()
    broker.register(
        CapabilityDefinition(
            name="runtime.noop", risk="none", approval_required=False,
            sandbox_required=False, rollback_supported=False, stable=True,
            description="Internal daemon health and queue validation task",
        ),
        lambda task: {"acknowledged": True, "parameters": task.parameters},
    )
    for definition in (
        CapabilityDefinition("process.run", "high", True, True, False, description="Execute an exact approved process"),
        CapabilityDefinition("filesystem.move", "high", True, False, True, description="Apply an exact approved file move plan"),
        CapabilityDefinition("browser.navigate", "medium", True, True, False, description="Navigate an approved browser session"),
        CapabilityDefinition("docker.run", "high", True, True, False, description="Run an approved isolated container"),
        CapabilityDefinition("git.commit", "medium", True, False, True, description="Create an approved Git commit"),
        CapabilityDefinition("deployment.publish", "critical", True, True, True, description="Publish an approved deployment"),
    ):
        broker.register(definition)
    return broker


def broker_receipt_json(receipt: BrokerReceipt) -> str:
    return json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n"

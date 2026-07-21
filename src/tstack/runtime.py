"""Runtime kernel primitives for capability-gated local execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

RUNTIME_REQUEST_SCHEMA = "tstack-runtime-request/v1"
RUNTIME_DECISION_SCHEMA = "tstack-runtime-decision/v1"
RUNTIME_AUDIT_SCHEMA = "tstack-runtime-audit/v1"

SENSITIVE_CAPABILITIES = {
    "filesystem.write",
    "filesystem.move",
    "filesystem.delete",
    "process.run",
    "browser.control",
    "network.access",
    "ssh.connect",
    "deploy.publish",
    "blender.control",
    "godot.build",
    "android.build",
    "xcode.build",
}

READ_ONLY_CAPABILITIES = {"filesystem.read", "project.scan", "knowledge.read", "environment.inspect"}


@dataclass(frozen=True)
class RuntimeRequest:
    schema: str
    request_id: str
    capability: str
    intent: str
    target: str | None
    reason: str
    risk: str
    approval_required: bool
    execution_allowed: bool
    request_hash: str


@dataclass(frozen=True)
class RuntimeDecision:
    schema: str
    request_id: str
    approved: bool
    approver: str
    reason: str
    request_hash: str
    execution_allowed: bool


@dataclass(frozen=True)
class RuntimeAuditEvent:
    schema: str
    event_id: str
    request_id: str
    capability: str
    outcome: str
    request_hash: str
    decision_hash: str | None
    timestamp_utc: str
    notes: tuple[str, ...]


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _hash(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _risk_for(capability: str, target: str | None) -> str:
    if capability in {"filesystem.delete", "ssh.connect", "deploy.publish", "xcode.build"}:
        return "high"
    if capability in SENSITIVE_CAPABILITIES:
        return "medium"
    if capability in READ_ONLY_CAPABILITIES:
        return "low"
    return "high"


def create_runtime_request(capability: str, intent: str, *, target: str | None = None, request_id: str = "RUNTIME-0001") -> RuntimeRequest:
    cap = capability.strip().lower()
    cleaned_intent = intent.strip()
    if not cap:
        raise ValueError("capability is required")
    if not cleaned_intent:
        raise ValueError("intent is required")
    risk = _risk_for(cap, target)
    approval_required = cap not in READ_ONLY_CAPABILITIES
    base = {
        "schema": RUNTIME_REQUEST_SCHEMA,
        "request_id": request_id,
        "capability": cap,
        "intent": cleaned_intent,
        "target": target,
        "reason": "Capability broker requires policy evaluation before any local action.",
        "risk": risk,
        "approval_required": approval_required,
        "execution_allowed": False,
    }
    return RuntimeRequest(**base, request_hash=_hash(base))


def approve_runtime_request(request_path: Path, *, approved: bool, approver: str, reason: str) -> RuntimeDecision:
    payload = json.loads(request_path.expanduser().resolve().read_text(encoding="utf-8"))
    if payload.get("schema") != RUNTIME_REQUEST_SCHEMA:
        raise ValueError("invalid runtime request schema")
    expected_hash = str(payload.get("request_hash", ""))
    unsigned = {key: payload[key] for key in payload if key != "request_hash"}
    if _hash(unsigned) != expected_hash:
        raise ValueError("runtime request hash mismatch")
    if not approver.strip():
        raise ValueError("approver is required")
    if not reason.strip():
        raise ValueError("decision reason is required")
    return RuntimeDecision(RUNTIME_DECISION_SCHEMA, str(payload["request_id"]), approved, approver.strip(), reason.strip(), expected_hash, False)


def create_audit_event(request_path: Path, decision_path: Path | None = None, *, outcome: str = "planned") -> RuntimeAuditEvent:
    request = json.loads(request_path.expanduser().resolve().read_text(encoding="utf-8"))
    if request.get("schema") != RUNTIME_REQUEST_SCHEMA:
        raise ValueError("invalid runtime request schema")
    decision_hash = None
    notes = ["runtime kernel is policy/audit foundation only", "no OS action was executed"]
    if decision_path is not None:
        decision = json.loads(decision_path.expanduser().resolve().read_text(encoding="utf-8"))
        if decision.get("schema") != RUNTIME_DECISION_SCHEMA:
            raise ValueError("invalid runtime decision schema")
        if decision.get("request_id") != request.get("request_id"):
            raise ValueError("runtime request and decision ids do not match")
        if decision.get("request_hash") != request.get("request_hash"):
            raise ValueError("runtime decision is not bound to request hash")
        decision_hash = _hash(decision)
        notes.append("decision hash is bound to request hash")
    event_id = hashlib.sha256(f"{request['request_id']}:{outcome}:{request['request_hash']}:{decision_hash or ''}".encode("utf-8")).hexdigest()[:16]
    return RuntimeAuditEvent(
        RUNTIME_AUDIT_SCHEMA,
        event_id,
        str(request["request_id"]),
        str(request["capability"]),
        outcome,
        str(request["request_hash"]),
        decision_hash,
        datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        tuple(notes),
    )


def runtime_json(item: RuntimeRequest | RuntimeDecision | RuntimeAuditEvent) -> str:
    return json.dumps(asdict(item), indent=2, sort_keys=True) + "\n"


def runtime_markdown(item: RuntimeRequest | RuntimeDecision | RuntimeAuditEvent) -> str:
    payload = asdict(item)
    title = payload["schema"].replace("tstack-", "").replace("/v1", "").replace("-", " ").title()
    lines = [f"# TStack {title}", ""]
    for key, value in payload.items():
        if isinstance(value, (list, tuple)):
            lines.append(f"- {key.replace('_', ' ').title()}:")
            lines.extend(f"  - {entry}" for entry in value)
        else:
            lines.append(f"- {key.replace('_', ' ').title()}: `{value}`")
    return "\n".join(lines) + "\n"

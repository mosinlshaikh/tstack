"""Cryptographically signed, action-bound runtime approvals.

This module binds human approval to the exact capability parameters that may be
executed. Approvals are short-lived, nonce-bearing, and designed for single-use
consumption by :mod:`tstack.runtime_store`.
"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ACTION_REQUEST_SCHEMA = "tstack-action-request/v1"
SIGNED_APPROVAL_SCHEMA = "tstack-signed-approval/v1"


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class ActionRequest:
    schema: str
    request_id: str
    workspace_id: str
    capability: str
    intent: str
    parameters: dict[str, Any]
    parameters_hash: str
    nonce: str
    created_at: str
    request_hash: str


@dataclass(frozen=True)
class SignedApproval:
    schema: str
    request_id: str
    request_hash: str
    parameters_hash: str
    approver: str
    key_id: str
    approved: bool
    reason: str
    issued_at: str
    expires_at: str
    max_uses: int
    nonce: str
    signature: str


def generate_signing_keypair() -> tuple[bytes, bytes, str]:
    """Return raw private/public Ed25519 keys and a stable public-key identifier.

    Production callers should store the private key in the operating system
    credential vault rather than in repository files.
    """

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = hashlib.sha256(public_raw).hexdigest()[:24]
    return private_raw, public_raw, key_id


def create_action_request(
    capability: str,
    intent: str,
    parameters: Mapping[str, Any],
    *,
    workspace_id: str,
    request_id: str | None = None,
    nonce: str | None = None,
    created_at: datetime | None = None,
) -> ActionRequest:
    cap = capability.strip().lower()
    cleaned_intent = intent.strip()
    cleaned_workspace = workspace_id.strip()
    if not cap:
        raise ValueError("capability is required")
    if not cleaned_intent:
        raise ValueError("intent is required")
    if not cleaned_workspace:
        raise ValueError("workspace_id is required")
    normalized_parameters = json.loads(json.dumps(dict(parameters), sort_keys=True))
    parameters_hash = _digest(normalized_parameters)
    created = (created_at or _utc_now()).astimezone(timezone.utc).replace(microsecond=0).isoformat()
    base = {
        "schema": ACTION_REQUEST_SCHEMA,
        "request_id": request_id or f"REQ-{secrets.token_hex(12)}",
        "workspace_id": cleaned_workspace,
        "capability": cap,
        "intent": cleaned_intent,
        "parameters": normalized_parameters,
        "parameters_hash": parameters_hash,
        "nonce": nonce or secrets.token_hex(16),
        "created_at": created,
    }
    return ActionRequest(**base, request_hash=_digest(base))


def _approval_unsigned_payload(approval: SignedApproval | Mapping[str, Any]) -> dict[str, Any]:
    payload = asdict(approval) if isinstance(approval, SignedApproval) else dict(approval)
    payload.pop("signature", None)
    return payload


def sign_action_request(
    request: ActionRequest,
    private_key_raw: bytes,
    *,
    approver: str,
    key_id: str,
    reason: str,
    approved: bool = True,
    ttl_seconds: int = 300,
    max_uses: int = 1,
    issued_at: datetime | None = None,
) -> SignedApproval:
    if not approver.strip():
        raise ValueError("approver is required")
    if not reason.strip():
        raise ValueError("reason is required")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    if max_uses != 1:
        raise ValueError("runtime v1 only supports single-use approvals")
    issued = (issued_at or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    unsigned = {
        "schema": SIGNED_APPROVAL_SCHEMA,
        "request_id": request.request_id,
        "request_hash": request.request_hash,
        "parameters_hash": request.parameters_hash,
        "approver": approver.strip(),
        "key_id": key_id.strip(),
        "approved": bool(approved),
        "reason": reason.strip(),
        "issued_at": issued.isoformat(),
        "expires_at": (issued + timedelta(seconds=ttl_seconds)).isoformat(),
        "max_uses": max_uses,
        "nonce": request.nonce,
    }
    signature = Ed25519PrivateKey.from_private_bytes(private_key_raw).sign(_canonical(unsigned))
    return SignedApproval(**unsigned, signature=base64.b64encode(signature).decode("ascii"))


def verify_action_request(request: ActionRequest | Mapping[str, Any]) -> ActionRequest:
    payload = asdict(request) if isinstance(request, ActionRequest) else dict(request)
    if payload.get("schema") != ACTION_REQUEST_SCHEMA:
        raise ValueError("invalid action request schema")
    supplied_request_hash = str(payload.get("request_hash", ""))
    unsigned = dict(payload)
    unsigned.pop("request_hash", None)
    if _digest(unsigned) != supplied_request_hash:
        raise ValueError("action request hash mismatch")
    parameters = payload.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("action request parameters must be an object")
    if _digest(parameters) != payload.get("parameters_hash"):
        raise ValueError("action parameter hash mismatch")
    return ActionRequest(**payload)


def verify_signed_approval(
    request: ActionRequest | Mapping[str, Any],
    approval: SignedApproval | Mapping[str, Any],
    public_key_raw: bytes,
    *,
    now: datetime | None = None,
) -> SignedApproval:
    checked_request = verify_action_request(request)
    payload = asdict(approval) if isinstance(approval, SignedApproval) else dict(approval)
    if payload.get("schema") != SIGNED_APPROVAL_SCHEMA:
        raise ValueError("invalid signed approval schema")
    if payload.get("request_id") != checked_request.request_id:
        raise ValueError("approval request id mismatch")
    if payload.get("request_hash") != checked_request.request_hash:
        raise ValueError("approval is not bound to request hash")
    if payload.get("parameters_hash") != checked_request.parameters_hash:
        raise ValueError("approval is not bound to exact action parameters")
    if payload.get("nonce") != checked_request.nonce:
        raise ValueError("approval nonce mismatch")
    if payload.get("approved") is not True:
        raise ValueError("action is not approved")
    if int(payload.get("max_uses", 0)) != 1:
        raise ValueError("approval must be single-use")
    current = (now or _utc_now()).astimezone(timezone.utc)
    issued = _parse_utc(str(payload.get("issued_at", "")))
    expires = _parse_utc(str(payload.get("expires_at", "")))
    if expires <= issued:
        raise ValueError("approval expiry must be after issue time")
    if current < issued:
        raise ValueError("approval is not valid yet")
    if current >= expires:
        raise ValueError("approval has expired")
    try:
        signature = base64.b64decode(str(payload.get("signature", "")), validate=True)
        Ed25519PublicKey.from_public_bytes(public_key_raw).verify(signature, _canonical(_approval_unsigned_payload(payload)))
    except (ValueError, InvalidSignature) as exc:
        raise ValueError("approval signature is invalid") from exc
    return SignedApproval(**payload)


def action_json(item: ActionRequest | SignedApproval) -> str:
    return json.dumps(asdict(item), indent=2, sort_keys=True) + "\n"

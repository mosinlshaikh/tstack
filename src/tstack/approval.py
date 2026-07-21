"""Approval-gated execution controls for TStack."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


APPROVAL_REQUEST_SCHEMA = "tstack-approval-request/v1"
APPROVAL_DECISION_SCHEMA = "tstack-approval-decision/v1"


@dataclass(frozen=True)
class ApprovalRequest:
    schema: str
    request_id: str
    action: str
    risk: str
    reason: str
    required_approver: str
    execution_allowed: bool
    approval_required: bool
    verification: str
    rollback: str


@dataclass(frozen=True)
class ApprovalDecision:
    schema: str
    request_id: str
    approved: bool
    execution_allowed: bool
    approver: str
    reason: str


def classify_risk(action: str) -> tuple[str, str]:
    text = action.lower()
    if any(term in text for term in ("deploy", "production", "ssh", "delete", "remove", "secret", "credential", "database migration", "payment", "auth")):
        return "high", "Action touches production, credentials, deletion, authentication, payments, SSH, or database migration risk."
    if any(term in text for term in ("dependency", "config", "ci", "docker", "kubernetes", "api", "schema")):
        return "medium", "Action may affect build, deployment, APIs, dependencies, or configuration."
    return "low", "Action appears limited and reversible, but still requires human approval."


def create_approval_request(action: str, *, request_id: str = "APPROVAL-0001") -> ApprovalRequest:
    cleaned = action.strip()
    if not cleaned:
        raise ValueError("approval action is required")
    risk, reason = classify_risk(cleaned)
    return ApprovalRequest(
        schema=APPROVAL_REQUEST_SCHEMA,
        request_id=request_id,
        action=cleaned,
        risk=risk,
        reason=reason,
        required_approver="human-owner",
        execution_allowed=False,
        approval_required=True,
        verification="Run relevant tests, scans, and post-change validation before marking complete.",
        rollback="Document rollback or recovery steps before execution is allowed.",
    )


def approval_request_json(request: ApprovalRequest) -> str:
    return json.dumps(asdict(request), indent=2, sort_keys=True) + "\n"


def approval_request_markdown(request: ApprovalRequest) -> str:
    return "\n".join(
        [
            "# TStack Approval Request",
            "",
            f"- Request ID: `{request.request_id}`",
            f"- Risk: `{request.risk}`",
            f"- Required approver: `{request.required_approver}`",
            f"- Approval required: {'yes' if request.approval_required else 'no'}",
            f"- Execution allowed: {'yes' if request.execution_allowed else 'no'}",
            "",
            "## Action",
            "",
            request.action,
            "",
            "## Reason",
            "",
            request.reason,
            "",
            "## Verification",
            "",
            request.verification,
            "",
            "## Rollback",
            "",
            request.rollback,
        ]
    ) + "\n"


def decide_approval(request_path: Path, *, approved: bool, approver: str, reason: str) -> ApprovalDecision:
    payload = json.loads(request_path.expanduser().resolve().read_text(encoding="utf-8"))
    if payload.get("schema") != APPROVAL_REQUEST_SCHEMA:
        raise ValueError("invalid approval request schema")
    name = approver.strip()
    if not name:
        raise ValueError("approver is required")
    why = reason.strip()
    if not why:
        raise ValueError("approval decision reason is required")
    # Approval records the human decision. Execution remains disabled until a
    # future executor separately verifies policy, risk, tests, and rollback.
    return ApprovalDecision(
        schema=APPROVAL_DECISION_SCHEMA,
        request_id=str(payload["request_id"]),
        approved=approved,
        execution_allowed=False,
        approver=name,
        reason=why,
    )


def approval_decision_json(decision: ApprovalDecision) -> str:
    return json.dumps(asdict(decision), indent=2, sort_keys=True) + "\n"


def approval_decision_markdown(decision: ApprovalDecision) -> str:
    return "\n".join(
        [
            "# TStack Approval Decision",
            "",
            f"- Request ID: `{decision.request_id}`",
            f"- Approved: {'yes' if decision.approved else 'no'}",
            f"- Approver: `{decision.approver}`",
            f"- Execution allowed: {'yes' if decision.execution_allowed else 'no'}",
            "",
            "## Reason",
            "",
            decision.reason,
        ]
    ) + "\n"

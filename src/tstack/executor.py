"""Controlled executor foundation for low-risk approved actions."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tstack.approval import APPROVAL_DECISION_SCHEMA, APPROVAL_REQUEST_SCHEMA


EXECUTION_PLAN_SCHEMA = "tstack-execution-plan/v1"


@dataclass(frozen=True)
class ExecutionPlan:
    schema: str
    request_id: str
    action: str
    risk: str
    approved: bool
    mode: str
    execution_allowed: bool
    executable: bool
    target_path: str | None
    blockers: tuple[str, ...]
    verification: tuple[str, ...]


def _load_pair(request_path: Path, decision_path: Path) -> tuple[dict, dict]:
    request = json.loads(request_path.expanduser().resolve().read_text(encoding="utf-8"))
    decision = json.loads(decision_path.expanduser().resolve().read_text(encoding="utf-8"))
    if request.get("schema") != APPROVAL_REQUEST_SCHEMA:
        raise ValueError("invalid approval request schema")
    if decision.get("schema") != APPROVAL_DECISION_SCHEMA:
        raise ValueError("invalid approval decision schema")
    if request.get("request_id") != decision.get("request_id"):
        raise ValueError("approval request and decision ids do not match")
    return request, decision


def plan_execution(request_path: Path, decision_path: Path, *, target: Path | None = None, apply: bool = False) -> ExecutionPlan:
    request, decision = _load_pair(request_path, decision_path)
    action = str(request["action"])
    risk = str(request["risk"])
    approved = bool(decision.get("approved"))
    blockers: list[str] = []
    target_path = str(target.expanduser().resolve()) if target else None
    lower = action.lower()
    doc_like = any(term in lower for term in ("readme", "docs", "documentation", "changelog"))

    if not approved:
        blockers.append("approval decision is not approved")
    if risk != "low":
        blockers.append("only low-risk actions are eligible for executor planning")
    if not doc_like:
        blockers.append("only documentation-like actions are eligible in executor foundation")
    if apply:
        blockers.append("apply mode is not enabled in executor foundation")

    executable = not blockers
    return ExecutionPlan(
        schema=EXECUTION_PLAN_SCHEMA,
        request_id=str(request["request_id"]),
        action=action,
        risk=risk,
        approved=approved,
        mode="apply" if apply else "dry-run",
        execution_allowed=False,
        executable=executable,
        target_path=target_path,
        blockers=tuple(blockers),
        verification=("review generated diff", "run tests", "run relevant validation command"),
    )


def execution_plan_json(plan: ExecutionPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def execution_plan_markdown(plan: ExecutionPlan) -> str:
    lines = [
        "# TStack Execution Plan",
        "",
        f"- Request ID: `{plan.request_id}`",
        f"- Risk: `{plan.risk}`",
        f"- Approved: {'yes' if plan.approved else 'no'}",
        f"- Mode: `{plan.mode}`",
        f"- Executable: {'yes' if plan.executable else 'no'}",
        f"- Execution allowed: {'yes' if plan.execution_allowed else 'no'}",
        f"- Target path: `{plan.target_path or 'not provided'}`",
        "",
        "## Action",
        "",
        plan.action,
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in plan.blockers or ("none",))
    lines.extend(["", "## Verification", ""])
    lines.extend(f"- {item}" for item in plan.verification)
    return "\n".join(lines) + "\n"

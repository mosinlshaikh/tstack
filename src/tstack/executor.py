"""Controlled executor foundation for low-risk approved actions."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tstack.approval import APPROVAL_DECISION_SCHEMA, APPROVAL_REQUEST_SCHEMA


EXECUTION_PLAN_SCHEMA = "tstack-execution-plan/v1"
EXECUTION_RESULT_SCHEMA = "tstack-execution-result/v1"


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


@dataclass(frozen=True)
class ExecutionResult:
    schema: str
    request_id: str
    applied: bool
    execution_allowed: bool
    target_path: str
    backup_path: str
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


def _backup_path(target: Path) -> Path:
    parent = target.parent
    candidate = parent / f"{target.name}.tstack.bak"
    index = 1
    while candidate.exists():
        candidate = parent / f"{target.name}.tstack.{index}.bak"
        index += 1
    return candidate


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
    if apply and target is None:
        blockers.append("apply mode requires a target path")
    if target is not None:
        resolved = target.expanduser().resolve()
        if resolved.suffix.lower() not in {".md", ".txt"}:
            blockers.append("executor foundation only supports .md and .txt targets")
        if apply and not resolved.exists():
            blockers.append("apply mode requires an existing target file")

    executable = not blockers
    return ExecutionPlan(
        schema=EXECUTION_PLAN_SCHEMA,
        request_id=str(request["request_id"]),
        action=action,
        risk=risk,
        approved=approved,
        mode="apply" if apply else "dry-run",
        execution_allowed=bool(apply and executable),
        executable=executable,
        target_path=target_path,
        blockers=tuple(blockers),
        verification=("review generated diff", "run tests", "run relevant validation command"),
    )


def apply_execution(request_path: Path, decision_path: Path, *, target: Path) -> ExecutionResult:
    plan = plan_execution(request_path, decision_path, target=target, apply=True)
    if not plan.executable or not plan.execution_allowed:
        raise ValueError("execution plan is blocked")
    resolved = target.expanduser().resolve()
    backup = _backup_path(resolved)
    original = resolved.read_text(encoding="utf-8")
    backup.write_text(original, encoding="utf-8")
    note = (
        "\n\n"
        "## TStack Executor Note\n\n"
        f"- Request ID: `{plan.request_id}`\n"
        f"- Approved low-risk action: {plan.action}\n"
        "- Execution mode: append-only documentation update.\n"
    )
    resolved.write_text(original.rstrip() + note, encoding="utf-8")
    return ExecutionResult(
        schema=EXECUTION_RESULT_SCHEMA,
        request_id=plan.request_id,
        applied=True,
        execution_allowed=True,
        target_path=str(resolved),
        backup_path=str(backup),
        verification=plan.verification,
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


def execution_result_json(result: ExecutionResult) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


def execution_result_markdown(result: ExecutionResult) -> str:
    lines = [
        "# TStack Execution Result",
        "",
        f"- Request ID: `{result.request_id}`",
        f"- Applied: {'yes' if result.applied else 'no'}",
        f"- Execution allowed: {'yes' if result.execution_allowed else 'no'}",
        f"- Target path: `{result.target_path}`",
        f"- Backup path: `{result.backup_path}`",
        "",
        "## Verification",
        "",
    ]
    lines.extend(f"- {item}" for item in result.verification)
    return "\n".join(lines) + "\n"

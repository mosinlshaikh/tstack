"""Explainable, human-approved decision planning for TStack.

The decision brain combines current scan findings with local learning memory. It
produces ranked remediation plans only. It never edits files, executes commands,
changes policy, opens network connections, or deploys software.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from tstack.learning import load_memory, recommendations

SEVERITY_WEIGHT = {"low": 1.0, "medium": 2.0, "high": 4.0, "critical": 8.0}


@dataclass(frozen=True)
class DecisionAction:
    action_id: str
    rule_id: str
    path: str | None
    severity: str
    priority: float
    confidence: float
    title: str
    rationale: str
    proposed_action: str
    verification: str
    approval_required: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True)
class DecisionPlan:
    schema: str
    source_fingerprint: str | None
    verdict: str
    total_findings: int
    actions: tuple[DecisionAction, ...]
    guardrails: tuple[str, ...]


def _finding_key(rule_id: str, path: str | None) -> tuple[str, str | None]:
    return rule_id, path


def build_plan(scan_payload: dict, memory: dict, *, limit: int = 20) -> DecisionPlan:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    findings = scan_payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("scan report requires a findings array")

    learned = {
        _finding_key(item.rule_id, item.path): item
        for item in recommendations(memory, minimum_occurrences=1)
    }
    actions: list[DecisionAction] = []
    for index, raw in enumerate(findings, start=1):
        if not isinstance(raw, dict) or not raw.get("rule_id"):
            raise ValueError("invalid finding in scan report")
        rule_id = str(raw["rule_id"])
        path = str(raw["path"]) if raw.get("path") is not None else None
        severity = str(raw.get("severity", "medium")).lower()
        if severity not in SEVERITY_WEIGHT:
            raise ValueError(f"unsupported severity: {severity}")

        learned_item = learned.get(_finding_key(rule_id, path))
        confidence = learned_item.confidence if learned_item else 0.5
        recurrence_bonus = learned_item.priority if learned_item else 0.0
        priority = SEVERITY_WEIGHT[severity] * (1.0 + confidence) + recurrence_bonus
        title = str(raw.get("title", rule_id))
        remediation = str(raw.get("remediation", "Review and resolve the finding."))
        evidence = str(raw.get("evidence", "Finding was reported by the scanner."))
        history = learned_item.rationale if learned_item else "No prior feedback history is available."
        rationale = f"{evidence} {history}"
        verification = f"Rerun the scanner and confirm {rule_id} is resolved without introducing new findings."
        actions.append(DecisionAction(
            action_id=f"DEC-{index:04d}",
            rule_id=rule_id,
            path=path,
            severity=severity,
            priority=round(priority, 4),
            confidence=round(confidence, 4),
            title=title,
            rationale=rationale,
            proposed_action=remediation,
            verification=verification,
        ))

    actions.sort(key=lambda item: (-item.priority, item.rule_id, item.path or ""))
    selected = tuple(actions[:limit])
    verdict = "HOLD" if any(item.severity == "critical" for item in selected) else "REVIEW" if selected else "PASS"
    return DecisionPlan(
        schema="tstack-decision-plan/v1",
        source_fingerprint=str(scan_payload.get("fingerprint")) if scan_payload.get("fingerprint") else None,
        verdict=verdict,
        total_findings=len(findings),
        actions=selected,
        guardrails=(
            "Human approval is required before every proposed action.",
            "The decision engine cannot execute commands or modify project files.",
            "No deployment, SSH, policy mutation, or credential access is permitted.",
            "Every approved action requires post-change verification and rollback readiness.",
        ),
    )


def build_plan_from_files(scan_path: Path, memory_path: Path, *, limit: int = 20) -> DecisionPlan:
    scan = json.loads(scan_path.expanduser().resolve().read_text(encoding="utf-8"))
    memory = load_memory(memory_path)
    return build_plan(scan, memory, limit=limit)


def plan_json(plan: DecisionPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def plan_markdown(plan: DecisionPlan) -> str:
    lines = [
        "# TStack Decision Plan",
        "",
        f"- **Verdict:** **{plan.verdict}**",
        f"- **Total findings:** {plan.total_findings}",
        f"- **Planned actions:** {len(plan.actions)}",
        f"- **Source fingerprint:** `{plan.source_fingerprint or 'not provided'}`",
        "",
        "## Ranked Actions",
        "",
    ]
    if not plan.actions:
        lines.append("No remediation actions are required.")
    for item in plan.actions:
        location = f" (`{item.path}`)" if item.path else ""
        lines.extend([
            f"### {item.action_id} — [{item.severity.upper()}] {item.rule_id}: {item.title}{location}",
            "",
            f"- Priority: {item.priority}",
            f"- Confidence: {item.confidence}",
            f"- Approval required: {'yes' if item.approval_required else 'no'}",
            f"- Autonomous execution allowed: {'yes' if item.execution_allowed else 'no'}",
            "",
            f"**Why:** {item.rationale}",
            "",
            f"**Proposed action:** {item.proposed_action}",
            "",
            f"**Verification:** {item.verification}",
            "",
        ])
    lines.extend(["## Guardrails", ""])
    lines.extend(f"- {item}" for item in plan.guardrails)
    lines.append("")
    return "\n".join(lines)

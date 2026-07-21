"""Bug finder and resolution planner."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tstack.agentic import route_failure
from tstack.scanner import scan_project


BUG_REPORT_SCHEMA = "tstack-bug-report/v1"


@dataclass(frozen=True)
class BugFinding:
    id: str
    severity: str
    title: str
    path: str | None
    evidence: str
    owner_agent: str
    proposed_fix: str
    verification: str


@dataclass(frozen=True)
class BugReport:
    schema: str
    root: str
    verdict: str
    findings: tuple[BugFinding, ...]
    execution_allowed: bool = False
    approval_required: bool = True


def find_bugs(root: Path, *, failure: str | None = None, max_files: int = 10000, max_file_bytes: int = 1000000) -> BugReport:
    base = root.expanduser().resolve()
    scan = scan_project(base, max_files=max_files, max_file_bytes=max_file_bytes)
    findings: list[BugFinding] = []

    if failure:
        route = route_failure(failure)
        findings.append(
            BugFinding(
                id="BUG-FAILURE-001",
                severity="high" if route.failure_type in {"security", "devops"} else "medium",
                title=f"Reported {route.failure_type} failure",
                path=None,
                evidence=failure,
                owner_agent=route.primary_agent,
                proposed_fix=f"Route to {route.primary_agent}, inspect failure logs, prepare minimal fix, and rerun verification.",
                verification=route.recommended_command,
            )
        )

    for index, item in enumerate(scan.findings, start=1):
        findings.append(
            BugFinding(
                id=f"BUG-SCAN-{index:03d}",
                severity=item.severity,
                title=item.title,
                path=item.path,
                evidence=item.evidence,
                owner_agent="security-agent" if item.severity in {"critical", "high"} else "qa-agent",
                proposed_fix=item.remediation,
                verification="Rerun tstack scan and relevant tests.",
            )
        )

    verdict = "HOLD" if any(item.severity == "critical" for item in findings) else "REVIEW" if findings else "PASS"
    return BugReport(BUG_REPORT_SCHEMA, str(base), verdict, tuple(findings))


def bug_report_json(report: BugReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def bug_report_markdown(report: BugReport) -> str:
    lines = [
        "# TStack Bug Report",
        "",
        f"- Root: `{report.root}`",
        f"- Verdict: **{report.verdict}**",
        f"- Findings: {len(report.findings)}",
        f"- Approval required: {'yes' if report.approval_required else 'no'}",
        f"- Execution allowed: {'yes' if report.execution_allowed else 'no'}",
        "",
        "## Findings",
        "",
    ]
    if not report.findings:
        lines.append("- No bug findings detected by current checks.")
    for item in report.findings:
        location = f" (`{item.path}`)" if item.path else ""
        lines.extend(
            [
                f"### {item.id} - [{item.severity.upper()}] {item.title}{location}",
                "",
                f"- Owner agent: `{item.owner_agent}`",
                f"- Evidence: {item.evidence}",
                f"- Proposed fix: {item.proposed_fix}",
                f"- Verification: {item.verification}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"

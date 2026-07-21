"""Policy evaluation, baselines, scan diffs, and SARIF export for TStack."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tstack.scanner import Finding, ScanReport

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
SARIF_LEVEL = {"low": "note", "medium": "warning", "high": "error", "critical": "error"}


@dataclass(frozen=True)
class Policy:
    fail_on: str = "critical"
    max_risk_score: int = 59
    allow_rules: tuple[str, ...] = ()
    allow_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyResult:
    passed: bool
    reasons: tuple[str, ...]
    active_findings: tuple[Finding, ...]
    suppressed_findings: tuple[Finding, ...]


@dataclass(frozen=True)
class ScanDiff:
    new: tuple[Finding, ...]
    resolved: tuple[Finding, ...]
    unchanged: tuple[Finding, ...]


def default_policy_json() -> str:
    return json.dumps({"fail_on": "critical", "max_risk_score": 59, "allow_rules": [], "allow_paths": []}, indent=2) + "\n"


def load_policy(project_root: Path, explicit: Path | None = None) -> Policy:
    path = explicit or (project_root / ".tstack" / "policy.json")
    if not path.exists():
        return Policy()
    payload = json.loads(path.read_text(encoding="utf-8"))
    fail_on = str(payload.get("fail_on", "critical")).lower()
    if fail_on not in SEVERITY_ORDER and fail_on != "never":
        raise ValueError("policy fail_on must be never, low, medium, high, or critical")
    max_risk = int(payload.get("max_risk_score", 59))
    if not 0 <= max_risk <= 100:
        raise ValueError("policy max_risk_score must be between 0 and 100")
    return Policy(fail_on, max_risk, tuple(payload.get("allow_rules", ())), tuple(payload.get("allow_paths", ())))


def _allowed(finding: Finding, policy: Policy) -> bool:
    if finding.rule_id in policy.allow_rules:
        return True
    if finding.path:
        return any(finding.path == prefix or finding.path.startswith(prefix.rstrip("/") + "/") for prefix in policy.allow_paths)
    return False


def evaluate_policy(report: ScanReport, policy: Policy) -> PolicyResult:
    suppressed = tuple(item for item in report.findings if _allowed(item, policy))
    active = tuple(item for item in report.findings if not _allowed(item, policy))
    reasons: list[str] = []
    if report.risk_score > policy.max_risk_score:
        reasons.append(f"risk score {report.risk_score} exceeds policy maximum {policy.max_risk_score}")
    if policy.fail_on != "never":
        threshold = SEVERITY_ORDER[policy.fail_on]
        blocking = [item for item in active if SEVERITY_ORDER[item.severity] >= threshold]
        if blocking:
            reasons.append(f"{len(blocking)} finding(s) meet or exceed severity threshold '{policy.fail_on}'")
    return PolicyResult(not reasons, tuple(reasons), active, suppressed)


def finding_key(finding: Finding) -> str:
    return "|".join((finding.rule_id, finding.severity, finding.path or "", finding.title))


def baseline_json(report: ScanReport) -> str:
    payload = {
        "schema": 1,
        "fingerprint": report.fingerprint,
        "findings": [finding_key(item) for item in report.findings],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def load_baseline(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != 1 or not isinstance(payload.get("findings"), list):
        raise ValueError("unsupported or invalid TStack baseline")
    return {str(item) for item in payload["findings"]}


def diff_report(report: ScanReport, baseline_keys: set[str]) -> ScanDiff:
    current = {finding_key(item): item for item in report.findings}
    new = tuple(current[key] for key in sorted(current.keys() - baseline_keys))
    unchanged = tuple(current[key] for key in sorted(current.keys() & baseline_keys))
    resolved = tuple(
        Finding(key.split("|", 3)[0], key.split("|", 3)[1], key.split("|", 3)[3], key.split("|", 3)[2] or None, "Present in baseline but not current scan.", "No action required; verify the resolution is intentional.")
        for key in sorted(baseline_keys - current.keys())
    )
    return ScanDiff(new, resolved, unchanged)


def diff_json(diff: ScanDiff) -> str:
    return json.dumps(asdict(diff), indent=2, sort_keys=True) + "\n"


def diff_markdown(diff: ScanDiff) -> str:
    lines = ["# TStack Scan Diff", "", f"- New: {len(diff.new)}", f"- Resolved: {len(diff.resolved)}", f"- Unchanged: {len(diff.unchanged)}", ""]
    for heading, items in (("New Findings", diff.new), ("Resolved Findings", diff.resolved)):
        lines.extend([f"## {heading}", ""])
        if not items:
            lines.append("None.")
        for item in items:
            location = f" (`{item.path}`)" if item.path else ""
            lines.append(f"- **{item.severity.upper()} {item.rule_id}** — {item.title}{location}")
        lines.append("")
    return "\n".join(lines)


def report_sarif(report: ScanReport, active_findings: tuple[Finding, ...] | None = None) -> str:
    findings = active_findings if active_findings is not None else report.findings
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for item in findings:
        rules.setdefault(item.rule_id, {
            "id": item.rule_id,
            "name": item.title,
            "shortDescription": {"text": item.title},
            "help": {"text": item.remediation},
            "defaultConfiguration": {"level": SARIF_LEVEL[item.severity]},
        })
        result: dict[str, Any] = {
            "ruleId": item.rule_id,
            "level": SARIF_LEVEL[item.severity],
            "message": {"text": f"{item.title}. {item.evidence}"},
        }
        if item.path:
            result["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": item.path}}}]
        results.append(result)
    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "TStack", "informationUri": "https://github.com/mosinlshaikh/tstack", "rules": list(rules.values())}},
            "results": results,
        }],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"

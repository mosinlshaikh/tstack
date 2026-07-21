"""Single-command release evidence orchestration for TStack."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tstack.policy import evaluate_policy, load_policy
from tstack.reproducible import compare_artifacts
from tstack.scanner import scan_project
from tstack.supplychain import verify_manifest
from tstack.trustgate import evaluate_release_trust


@dataclass(frozen=True)
class ReleaseStage:
    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class ReleaseDecision:
    passed: bool
    verdict: str
    repository: str
    commit: str
    stages: tuple[ReleaseStage, ...]


def evaluate_release(
    project: Path,
    release_dir: Path,
    rebuilt_dir: Path,
    *,
    repository: str,
    workflow: str,
    commit: str,
    require_attestation_receipt: bool = True,
) -> ReleaseDecision:
    project_root = project.expanduser().resolve()
    release_root = release_dir.expanduser().resolve()
    rebuilt_root = rebuilt_dir.expanduser().resolve()

    scan = scan_project(project_root)
    policy = load_policy(project_root)
    policy_result = evaluate_policy(scan, policy)
    manifest_result = verify_manifest(release_root)
    reproducible = compare_artifacts(release_root, rebuilt_root)
    trust = evaluate_release_trust(
        release_root,
        repository=repository,
        workflow=workflow,
        commit=commit,
        require_attestation_receipt=require_attestation_receipt,
    )

    stages = (
        ReleaseStage("project-policy", policy_result.passed, f"active={len(policy_result.active_findings)} suppressed={len(policy_result.suppressed_findings)}"),
        ReleaseStage("artifact-integrity", manifest_result.valid, f"checked={manifest_result.checked} missing={len(manifest_result.missing)} mismatched={len(manifest_result.mismatched)}"),
        ReleaseStage("reproducible-build", reproducible.passed, f"checked={reproducible.checked} mismatched={len(reproducible.mismatched)}"),
        ReleaseStage("release-trust", trust.passed, trust.verdict),
    )
    passed = all(stage.passed for stage in stages)
    return ReleaseDecision(passed, "PASS" if passed else "HOLD", repository, commit.lower(), stages)


def release_json(result: ReleaseDecision) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


def release_markdown(result: ReleaseDecision) -> str:
    lines = [
        "# TStack Release Decision",
        "",
        f"- **Verdict:** **{result.verdict}**",
        f"- **Repository:** `{result.repository}`",
        f"- **Commit:** `{result.commit}`",
        "",
        "## Stages",
        "",
    ]
    lines.extend(f"- {'PASS' if stage.passed else 'FAIL'} — {stage.name}: {stage.evidence}" for stage in result.stages)
    lines.extend(["", "A release may proceed only when every stage passes.", ""])
    return "\n".join(lines)

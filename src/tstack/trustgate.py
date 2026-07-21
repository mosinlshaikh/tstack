"""End-to-end release trust gate for TStack."""

from __future__ import annotations
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from tstack.supplychain import verify_manifest

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class GateCheck:
    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class TrustGateResult:
    passed: bool
    verdict: str
    repository: str
    workflow: str
    commit: str
    checks: tuple[GateCheck, ...]
    attestation_command: str


def _validate_receipt(path: Path, repository: str, workflow: str, artifacts: list[str]) -> GateCheck:
    if not path.is_file():
        return GateCheck("attestation-receipt", False, "attestation-verification.json missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return GateCheck("attestation-receipt", False, f"invalid receipt: {exc}")
    expected_artifact = artifacts[0] if artifacts else None
    passed = (
        payload.get("schema") == "tstack-attestation-receipt/v1"
        and payload.get("verified") is True
        and payload.get("repository") == repository
        and payload.get("workflow") == workflow
        and isinstance(payload.get("verification_results"), list)
        and bool(payload.get("verification_results"))
        and (expected_artifact is None or payload.get("artifact") == expected_artifact)
    )
    return GateCheck(
        "attestation-receipt",
        passed,
        "verified receipt identity matches release" if passed else "receipt schema or release identity mismatch",
    )


def evaluate_release_trust(
    directory: Path,
    *,
    repository: str,
    workflow: str,
    commit: str,
    require_attestation_receipt: bool = False,
) -> TrustGateResult:
    root = directory.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"release directory not found: {root}")
    if not REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must use owner/name form")
    if not workflow.startswith(".github/workflows/") or not workflow.endswith((".yml", ".yaml")):
        raise ValueError("workflow must be a .github/workflows/*.yml path")
    if not COMMIT_RE.fullmatch(commit.lower()):
        raise ValueError("commit must be a full 40-character lowercase hexadecimal SHA")

    verification = verify_manifest(root)
    manifest = root / "manifest.json"
    sbom = root / "sbom.cdx.json"
    sha256 = root / "checksums.sha256"
    sha3 = root / "checksums.sha3-256"
    receipt = root / "attestation-verification.json"

    artifacts: list[str] = []
    if manifest.is_file():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        artifacts = [item["path"] for item in payload.get("artifacts", []) if isinstance(item, dict) and item.get("path")]

    checks = [
        GateCheck("manifest-integrity", verification.valid, f"checked={verification.checked}; missing={len(verification.missing)}; mismatched={len(verification.mismatched)}"),
        GateCheck("sha256-checksums", sha256.is_file(), "checksums.sha256 present" if sha256.is_file() else "checksums.sha256 missing"),
        GateCheck("sha3-256-checksums", sha3.is_file(), "checksums.sha3-256 present" if sha3.is_file() else "checksums.sha3-256 missing"),
        GateCheck("sbom", sbom.is_file(), "CycloneDX SBOM present" if sbom.is_file() else "sbom.cdx.json missing"),
        GateCheck("repository-identity", True, repository),
        GateCheck("workflow-identity", True, workflow),
        GateCheck("commit-identity", True, commit.lower()),
    ]
    if require_attestation_receipt:
        checks.append(_validate_receipt(receipt, repository, workflow, artifacts))

    subject = artifacts[0] if artifacts else "<artifact>"
    command = (
        f"gh attestation verify {subject} -R {repository} "
        f"--signer-workflow {repository}/{workflow} --source-digest {commit.lower()} "
        f"--deny-self-hosted-runners --format json"
    )
    passed = all(item.passed for item in checks)
    return TrustGateResult(passed, "PASS" if passed else "HOLD", repository, workflow, commit.lower(), tuple(checks), command)


def trust_gate_json(result: TrustGateResult) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


def trust_gate_markdown(result: TrustGateResult) -> str:
    lines = [
        "# TStack Release Trust Gate", "",
        f"- **Verdict:** **{result.verdict}**",
        f"- **Repository:** `{result.repository}`",
        f"- **Workflow:** `{result.workflow}`",
        f"- **Commit:** `{result.commit}`", "", "## Checks", "",
    ]
    lines.extend(f"- {'PASS' if item.passed else 'FAIL'} — {item.name}: {item.evidence}" for item in result.checks)
    lines.extend(["", "## Attestation Verification", "", "```bash", result.attestation_command, "```", ""])
    return "\n".join(lines)

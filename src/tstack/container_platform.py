"""Dependency-free Docker and Kubernetes security auditing for TStack."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
WEIGHTS = {"critical": 30, "high": 15, "medium": 7, "low": 2}


@dataclass(frozen=True)
class PlatformFinding:
    rule_id: str
    severity: str
    title: str
    path: str
    evidence: str
    remediation: str


@dataclass(frozen=True)
class PlatformReport:
    root: str
    docker_detected: bool
    kubernetes_detected: bool
    files_checked: tuple[str, ...]
    findings: tuple[PlatformFinding, ...]
    risk_score: int
    verdict: str


def _finding(rule_id: str, severity: str, title: str, path: Path, root: Path, evidence: str, remediation: str) -> PlatformFinding:
    return PlatformFinding(rule_id, severity, title, path.relative_to(root).as_posix(), evidence, remediation)


def _docker_checks(root: Path, path: Path, text: str) -> list[PlatformFinding]:
    findings: list[PlatformFinding] = []
    lines = text.splitlines()
    from_lines = [line.strip() for line in lines if line.strip().upper().startswith("FROM ")]
    if any(re.search(r"(?i)\bFROM\s+[^\s:@]+(?::latest)?(?:\s|$)", line) and "@sha256:" not in line for line in from_lines):
        findings.append(_finding("DOCKER001", "high", "Base image is not digest pinned", path, root, "A FROM instruction does not use an immutable sha256 digest.", "Pin production base images by digest and update them through an audited dependency process."))
    if not any(line.strip().upper().startswith("USER ") for line in lines):
        findings.append(_finding("DOCKER002", "high", "Container user is not declared", path, root, "No USER instruction was detected.", "Create a dedicated non-root user and switch to it in the final runtime stage."))
    if re.search(r"(?im)^\s*(?:ADD|COPY)\s+\.\s+", text):
        findings.append(_finding("DOCKER003", "medium", "Broad build-context copy detected", path, root, "ADD/COPY copies the entire context.", "Use a strict .dockerignore and copy only required manifests and source paths."))
    if re.search(r"(?im)^\s*ADD\s+https?://", text):
        findings.append(_finding("DOCKER004", "high", "Remote ADD detected", path, root, "Dockerfile downloads a remote URL with ADD.", "Download with a pinned tool, verify a cryptographic digest, then copy the verified artifact."))
    if re.search(r"(?i)(?:apt-get\s+upgrade|apk\s+upgrade|yum\s+update)", text):
        findings.append(_finding("DOCKER005", "medium", "Unbounded package upgrade detected", path, root, "A package-manager upgrade/update command was detected.", "Use a maintained pinned base image and install only explicitly required packages."))
    if not any(line.strip().upper().startswith("HEALTHCHECK ") for line in lines):
        findings.append(_finding("DOCKER006", "low", "Container health check missing", path, root, "No HEALTHCHECK instruction was detected.", "Add a deterministic health check or document that orchestration probes are authoritative."))
    if len(from_lines) < 2:
        findings.append(_finding("DOCKER007", "low", "Single-stage image build", path, root, "Only one FROM instruction was detected.", "Use a multi-stage build when build tooling is not required at runtime."))
    return findings


def _k8s_checks(root: Path, path: Path, text: str) -> list[PlatformFinding]:
    findings: list[PlatformFinding] = []
    lower = text.lower()
    workload = bool(re.search(r"(?m)^kind:\s*(deployment|statefulset|daemonset|job|cronjob)\s*$", lower))
    if not workload:
        return findings
    if "runasnonroot:" not in lower:
        findings.append(_finding("K8S001", "high", "runAsNonRoot is missing", path, root, "Workload manifest does not declare runAsNonRoot: true.", "Set pod/container securityContext.runAsNonRoot to true and use a compatible image user."))
    if "allowprivilegeescalation: false" not in lower:
        findings.append(_finding("K8S002", "high", "Privilege escalation is not disabled", path, root, "allowPrivilegeEscalation: false was not detected.", "Set container securityContext.allowPrivilegeEscalation to false."))
    if "privileged: true" in lower:
        findings.append(_finding("K8S003", "critical", "Privileged container detected", path, root, "The workload explicitly enables privileged mode.", "Remove privileged mode; isolate unavoidable host-level agents with dedicated nodes and policy exceptions."))
    if "readOnlyRootFilesystem: true".lower() not in lower:
        findings.append(_finding("K8S004", "medium", "Read-only root filesystem missing", path, root, "readOnlyRootFilesystem: true was not detected.", "Enable a read-only root filesystem and mount explicit writable volumes where required."))
    if "capabilities:" not in lower or "drop:" not in lower or "- all" not in lower:
        findings.append(_finding("K8S005", "high", "Linux capabilities are not fully dropped", path, root, "A drop: [ALL] equivalent was not detected.", "Drop ALL Linux capabilities and add back only narrowly justified capabilities."))
    if "resources:" not in lower or "limits:" not in lower or "requests:" not in lower:
        findings.append(_finding("K8S006", "high", "Resource requests or limits missing", path, root, "Complete requests and limits were not detected.", "Declare CPU and memory requests and limits for every application container."))
    if "readinessprobe:" not in lower:
        findings.append(_finding("K8S007", "medium", "Readiness probe missing", path, root, "No readinessProbe was detected.", "Add a readiness probe that reflects ability to serve production traffic."))
    if "livenessprobe:" not in lower:
        findings.append(_finding("K8S008", "low", "Liveness probe missing", path, root, "No livenessProbe was detected.", "Add a conservative liveness probe or explicitly document why it is unsafe."))
    if re.search(r"(?im)^\s*image:\s*[^\s@]+:latest\s*$", text):
        findings.append(_finding("K8S009", "high", "Mutable latest image tag detected", path, root, "A workload image uses the latest tag.", "Deploy an immutable image digest or a controlled version tag plus admission verification."))
    if "automountserviceaccounttoken: false" not in lower:
        findings.append(_finding("K8S010", "medium", "Service-account token automount not disabled", path, root, "automountServiceAccountToken: false was not detected.", "Disable token automount unless the workload calls the Kubernetes API."))
    return findings


def audit_platform(path: Path) -> PlatformReport:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project directory not found: {root}")
    checked: list[str] = []
    findings: list[PlatformFinding] = []
    docker_detected = kubernetes_detected = False
    for item in sorted(root.rglob("*")):
        if not item.is_file() or any(part in {".git", "node_modules", ".venv", "venv", "dist", "build", "target"} for part in item.relative_to(root).parts):
            continue
        name = item.name.lower()
        is_docker = name == "dockerfile" or name.startswith("dockerfile.")
        is_yaml = item.suffix.lower() in {".yml", ".yaml"}
        if not is_docker and not is_yaml:
            continue
        try:
            text = item.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if is_docker:
            docker_detected = True
            checked.append(item.relative_to(root).as_posix())
            findings.extend(_docker_checks(root, item, text))
        elif re.search(r"(?m)^apiVersion:\s*[^\s]+\s*$", text) and re.search(r"(?m)^kind:\s*[^\s]+\s*$", text):
            kubernetes_detected = True
            checked.append(item.relative_to(root).as_posix())
            findings.extend(_k8s_checks(root, item, text))
    if docker_detected and not (root / ".dockerignore").is_file():
        findings.append(PlatformFinding("DOCKER008", "high", ".dockerignore missing", ".dockerignore", "Docker is present but .dockerignore was not found.", "Add a deny-oriented .dockerignore covering VCS data, secrets, caches, dependencies, and build output."))
    if kubernetes_detected:
        paths = {item.relative_to(root).as_posix().lower() for item in root.rglob("*") if item.is_file()}
        if not any("networkpol" in value for value in paths):
            findings.append(PlatformFinding("K8S011", "high", "NetworkPolicy not detected", "k8s/", "No NetworkPolicy-like manifest filename was detected.", "Add default-deny ingress/egress policies and explicit application flows."))
        if not any("poddisruptionbudget" in value or "pdb" in Path(value).name for value in paths):
            findings.append(PlatformFinding("K8S012", "medium", "PodDisruptionBudget not detected", "k8s/", "No PodDisruptionBudget-like manifest filename was detected.", "Add a PodDisruptionBudget for replicated availability-sensitive workloads."))
    findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.rule_id, item.path))
    score = min(100, sum(WEIGHTS[item.severity] for item in findings))
    verdict = "HOLD" if any(item.severity == "critical" for item in findings) or score >= 60 else "REVIEW" if score >= 20 else "PASS"
    return PlatformReport(str(root), docker_detected, kubernetes_detected, tuple(sorted(set(checked))), tuple(findings), score, verdict)


def platform_json(report: PlatformReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def platform_markdown(report: PlatformReport) -> str:
    lines = ["# TStack Container Platform Audit", "", f"- **Verdict:** **{report.verdict}**", f"- **Risk score:** {report.risk_score}/100", f"- **Docker detected:** {report.docker_detected}", f"- **Kubernetes detected:** {report.kubernetes_detected}", "", "## Findings", ""]
    if not report.findings:
        lines.append("No container-platform findings.")
    for item in report.findings:
        lines.extend([f"### [{item.severity.upper()}] {item.rule_id}: {item.title} — `{item.path}`", "", f"**Evidence:** {item.evidence}", "", f"**Remediation:** {item.remediation}", ""])
    return "\n".join(lines)

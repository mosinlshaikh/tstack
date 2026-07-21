"""Deterministic, dependency-free project scanner for TStack."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

IGNORED_DIRS = {".git", ".hg", ".svn", ".tox", ".venv", "venv", "node_modules", "dist", "build", "target", "__pycache__", ".idea", ".vscode"}
TEXT_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".go", ".rs", ".php", ".rb", ".cs", ".c", ".h", ".cpp", ".hpp", ".html", ".css", ".scss", ".sql", ".sh", ".ps1", ".yml", ".yaml", ".toml", ".json", ".xml", ".md", ".txt", ".env"}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".go": "Go", ".rs": "Rust", ".php": "PHP",
    ".rb": "Ruby", ".cs": "C#", ".c": "C", ".h": "C/C++", ".cpp": "C++", ".hpp": "C++",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell",
}
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("generic-secret", re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"\n]{8,}['\"]")),
)

@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    path: str | None
    evidence: str
    remediation: str

@dataclass(frozen=True)
class ScanReport:
    root: str
    fingerprint: str
    files_scanned: int
    bytes_scanned: int
    languages: dict[str, int]
    controls: dict[str, bool]
    findings: tuple[Finding, ...]
    risk_score: int
    verdict: str


def _iter_files(root: Path, max_files: int, max_file_bytes: int):
    count = 0
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if not path.is_file() or path.is_symlink() or path.stat().st_size > max_file_bytes:
            continue
        count += 1
        if count > max_files:
            raise ValueError(f"scan file limit exceeded ({max_files})")
        yield path


def scan_project(path: Path, *, max_files: int = 10000, max_file_bytes: int = 1_000_000) -> ScanReport:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project directory not found: {root}")

    languages: Counter[str] = Counter()
    findings: list[Finding] = []
    digest = hashlib.sha256()
    files_scanned = bytes_scanned = 0
    relative_files: set[str] = set()

    for file_path in _iter_files(root, max_files, max_file_bytes):
        relative = file_path.relative_to(root).as_posix()
        relative_files.add(relative)
        data = file_path.read_bytes()
        files_scanned += 1
        bytes_scanned += len(data)
        digest.update(relative.encode("utf-8")); digest.update(b"\0"); digest.update(data); digest.update(b"\0")
        language = LANGUAGES.get(file_path.suffix.lower())
        if language:
            languages[language] += 1
        if file_path.name.startswith(".env") and file_path.name not in {".env.example", ".env.sample"}:
            findings.append(Finding("SEC001", "high", "Environment secrets file present", relative, "Potential live secrets file is inside the project tree.", "Remove it from version control, rotate exposed values, and keep only a redacted example."))
        if file_path.suffix.lower() not in TEXT_EXTENSIONS and file_path.name not in {"Dockerfile", "Makefile"}:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for rule_id, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(Finding("SEC002", "critical", f"Possible embedded secret: {rule_id}", relative, "A secret-like credential pattern matched file content.", "Verify immediately; remove and rotate any real credential. Use environment or secret-manager injection."))
                break
        if len(text.splitlines()) > 1500:
            findings.append(Finding("ARC001", "medium", "Oversized source file", relative, f"File has {len(text.splitlines())} lines.", "Split by responsibility and add focused tests before refactoring."))

    names = {Path(item).name.lower() for item in relative_files}
    controls = {
        "readme": any(name.startswith("readme") for name in names),
        "license": any(name.startswith("license") or name.startswith("copying") for name in names),
        "gitignore": ".gitignore" in relative_files,
        "tests": any(part.lower() in {"test", "tests", "spec", "specs"} for item in relative_files for part in Path(item).parts[:-1]),
        "ci": any(item.startswith(".github/workflows/") or item in {".gitlab-ci.yml", "azure-pipelines.yml"} for item in relative_files),
        "security_policy": any(item.lower() == "security.md" or item.lower() == ".github/security.md" for item in relative_files),
        "dependency_lock": any(name in names for name in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "pipfile.lock", "cargo.lock", "go.sum", "gradle.lockfile"}),
    }
    control_rules = {
        "readme": ("DOC001", "low", "README missing", "Add purpose, setup, usage, architecture, and support information."),
        "license": ("GOV001", "medium", "License missing", "Select and add an explicit license before public distribution."),
        "gitignore": ("OPS001", "medium", ".gitignore missing", "Add language-appropriate ignores for secrets, builds, caches, and local tooling."),
        "tests": ("QA001", "high", "Automated tests not detected", "Add deterministic tests for critical behavior and regressions."),
        "ci": ("OPS002", "high", "CI workflow not detected", "Run lint, tests, build, and security checks on pull requests."),
        "security_policy": ("SEC003", "low", "Security policy missing", "Document responsible disclosure and supported versions."),
        "dependency_lock": ("SUP001", "medium", "Dependency lockfile not detected", "Commit a lockfile where the ecosystem supports one for reproducible builds."),
    }
    for key, present in controls.items():
        if not present:
            rule, severity, title, remediation = control_rules[key]
            findings.append(Finding(rule, severity, title, None, f"Control '{key}' was not detected.", remediation))

    weights = {"low": 2, "medium": 7, "high": 15, "critical": 30}
    risk_score = min(100, sum(weights[item.severity] for item in findings))
    verdict = "HOLD" if any(item.severity == "critical" for item in findings) or risk_score >= 60 else "REVIEW" if risk_score >= 20 else "PASS"
    findings.sort(key=lambda item: ({"critical": 0, "high": 1, "medium": 2, "low": 3}[item.severity], item.rule_id, item.path or ""))
    return ScanReport(str(root), digest.hexdigest(), files_scanned, bytes_scanned, dict(languages.most_common()), controls, tuple(findings), risk_score, verdict)


def report_json(report: ScanReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def report_markdown(report: ScanReport) -> str:
    lines = ["# TStack Project Audit", "", f"- **Root:** `{report.root}`", f"- **Fingerprint:** `{report.fingerprint}`", f"- **Files scanned:** {report.files_scanned}", f"- **Bytes scanned:** {report.bytes_scanned}", f"- **Risk score:** {report.risk_score}/100", f"- **Verdict:** **{report.verdict}**", "", "## Languages", ""]
    lines.extend([f"- {name}: {count} files" for name, count in report.languages.items()] or ["- No recognized source languages detected."])
    lines.extend(["", "## Engineering Controls", ""])
    lines.extend(f"- {'PASS' if value else 'MISSING'} — {name.replace('_', ' ')}" for name, value in report.controls.items())
    lines.extend(["", "## Findings", ""])
    if not report.findings:
        lines.append("No findings.")
    for finding in report.findings:
        location = f" — `{finding.path}`" if finding.path else ""
        lines.extend([f"### [{finding.severity.upper()}] {finding.rule_id}: {finding.title}{location}", "", f"**Evidence:** {finding.evidence}", "", f"**Remediation:** {finding.remediation}", ""])
    lines.extend(["## Decision", "", "Critical findings or a risk score of 60+ produce HOLD. Resolve findings and rerun the same deterministic scan before release.", ""])
    return "\n".join(lines)

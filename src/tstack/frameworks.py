"""Framework-aware static checks used by the TStack scanner."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class FrameworkFinding:
    rule_id: str
    severity: str
    title: str
    path: str | None
    evidence: str
    remediation: str


@dataclass(frozen=True)
class FrameworkProfile:
    name: str
    detected: bool
    evidence: tuple[str, ...]
    checks_run: int


def _exists(files: set[str], *candidates: str) -> bool:
    return any(candidate in files for candidate in candidates)


def _has_prefix(files: set[str], *prefixes: str) -> bool:
    return any(any(item.startswith(prefix) for prefix in prefixes) for item in files)


def _read_text(root: Path, relative: str, limit: int = 1_000_000) -> str:
    path = root / relative
    if not path.is_file() or path.stat().st_size > limit:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _finding(rule_id: str, severity: str, title: str, path: str | None, evidence: str, remediation: str) -> FrameworkFinding:
    return FrameworkFinding(rule_id, severity, title, path, evidence, remediation)


def _python(root: Path, files: set[str]) -> tuple[FrameworkProfile, list[FrameworkFinding]]:
    markers = [item for item in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile") if item in files]
    detected = bool(markers or any(item.endswith(".py") for item in files))
    findings: list[FrameworkFinding] = []
    if not detected:
        return FrameworkProfile("Python", False, (), 0), findings
    checks = 4
    if not _exists(files, "pyproject.toml", "setup.cfg", "tox.ini"):
        findings.append(_finding("PY001", "medium", "Python project configuration missing", None, "No pyproject.toml, setup.cfg, or tox.ini was detected.", "Centralize build, lint, test, and packaging configuration in pyproject.toml."))
    if not _exists(files, "requirements.txt", "requirements-dev.txt", "poetry.lock", "Pipfile.lock", "uv.lock") and "pyproject.toml" not in files:
        findings.append(_finding("PY002", "medium", "Python dependencies are not declared", None, "No supported dependency manifest was detected.", "Declare runtime and development dependencies and commit a reproducible lockfile."))
    if not any(Path(item).name.startswith("test_") and item.endswith(".py") for item in files):
        findings.append(_finding("PY003", "high", "Python tests not detected", None, "No test_*.py files were found.", "Add pytest or unittest coverage for critical paths and failure modes."))
    if "pyproject.toml" in files:
        text = _read_text(root, "pyproject.toml")
        if text and not re.search(r"(?m)^requires-python\s*=", text):
            findings.append(_finding("PY004", "low", "Python version constraint missing", "pyproject.toml", "The project metadata does not declare requires-python.", "Declare the supported Python version range to prevent incompatible installs."))
    return FrameworkProfile("Python", True, tuple(markers), checks), findings


def _node(root: Path, files: set[str]) -> tuple[FrameworkProfile, list[FrameworkFinding]]:
    detected = "package.json" in files
    findings: list[FrameworkFinding] = []
    if not detected:
        return FrameworkProfile("Node.js", False, (), 0), findings
    checks = 5
    text = _read_text(root, "package.json")
    try:
        package = json.loads(text) if text else {}
    except json.JSONDecodeError:
        package = {}
        findings.append(_finding("NODE001", "high", "Invalid package.json", "package.json", "package.json could not be parsed as JSON.", "Repair the manifest before dependency installation or release."))
    if not _exists(files, "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"):
        findings.append(_finding("NODE002", "high", "Node lockfile missing", None, "No supported Node.js lockfile was detected.", "Commit exactly one package-manager lockfile for reproducible installs."))
    scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
    if not isinstance(scripts, dict) or "test" not in scripts:
        findings.append(_finding("NODE003", "high", "Node test script missing", "package.json", "package.json does not define scripts.test.", "Add a deterministic test command suitable for local and CI execution."))
    if not isinstance(scripts, dict) or not any(name in scripts for name in ("lint", "check", "typecheck")):
        findings.append(_finding("NODE004", "medium", "Node static-check script missing", "package.json", "No lint, check, or typecheck script was found.", "Add linting and, for TypeScript, type checking to the CI quality gate."))
    engines = package.get("engines", {}) if isinstance(package, dict) else {}
    if not isinstance(engines, dict) or "node" not in engines:
        findings.append(_finding("NODE005", "low", "Node engine constraint missing", "package.json", "package.json does not constrain the Node.js runtime.", "Declare engines.node and align it with the CI matrix and deployment runtime."))
    return FrameworkProfile("Node.js", True, ("package.json",), checks), findings


def _android(root: Path, files: set[str]) -> tuple[FrameworkProfile, list[FrameworkFinding]]:
    evidence = tuple(item for item in ("settings.gradle", "settings.gradle.kts", "gradlew", "gradlew.bat") if item in files)
    detected = bool(evidence and (_has_prefix(files, "app/src/") or any(item.endswith((".kt", ".java")) for item in files)))
    findings: list[FrameworkFinding] = []
    if not detected:
        return FrameworkProfile("Android", False, (), 0), findings
    checks = 5
    if not _exists(files, "gradlew", "gradlew.bat"):
        findings.append(_finding("AND001", "high", "Gradle wrapper missing", None, "Android project detected without a Gradle wrapper.", "Commit gradlew, gradlew.bat, and gradle/wrapper files for reproducible builds."))
    if not any(item.endswith("AndroidManifest.xml") for item in files):
        findings.append(_finding("AND002", "critical", "Android manifest missing", None, "No AndroidManifest.xml was detected.", "Add and validate the application manifest before attempting a build or release."))
    if not _has_prefix(files, "app/src/test/", "app/src/androidTest/"):
        findings.append(_finding("AND003", "high", "Android tests not detected", None, "No app/src/test or app/src/androidTest files were detected.", "Add unit and instrumentation coverage for critical user and platform flows."))
    gradle_files = [item for item in files if item.endswith(("build.gradle", "build.gradle.kts"))]
    joined = "\n".join(_read_text(root, item) for item in gradle_files[:10])
    if joined and "minSdk" not in joined:
        findings.append(_finding("AND004", "medium", "Android minSdk not detected", gradle_files[0] if gradle_files else None, "Gradle configuration did not expose a minSdk declaration.", "Declare and document minSdk, targetSdk, and compileSdk compatibility."))
    if not _exists(files, "proguard-rules.pro"):
        findings.append(_finding("AND005", "low", "Android shrinker rules missing", None, "No proguard-rules.pro was detected.", "Add explicit R8/ProGuard rules when producing optimized release builds."))
    return FrameworkProfile("Android", True, evidence, checks), findings


def _php(root: Path, files: set[str]) -> tuple[FrameworkProfile, list[FrameworkFinding]]:
    detected = "composer.json" in files or any(item.endswith(".php") for item in files)
    findings: list[FrameworkFinding] = []
    if not detected:
        return FrameworkProfile("PHP", False, (), 0), findings
    checks = 4
    if "composer.json" not in files:
        findings.append(_finding("PHP001", "high", "Composer manifest missing", None, "PHP source was detected without composer.json.", "Define dependencies, autoloading, scripts, and platform constraints in composer.json."))
    if "composer.json" in files and "composer.lock" not in files:
        findings.append(_finding("PHP002", "medium", "Composer lockfile missing", None, "composer.json exists but composer.lock was not detected.", "Commit composer.lock for applications to ensure reproducible dependency resolution."))
    if not _has_prefix(files, "tests/", "test/"):
        findings.append(_finding("PHP003", "high", "PHP tests not detected", None, "No tests/ or test/ tree was detected.", "Add PHPUnit or Pest tests for business-critical and security-sensitive behavior."))
    if "composer.json" in files:
        text = _read_text(root, "composer.json")
        try:
            composer = json.loads(text) if text else {}
        except json.JSONDecodeError:
            composer = {}
            findings.append(_finding("PHP004", "high", "Invalid composer.json", "composer.json", "composer.json could not be parsed as JSON.", "Repair the manifest and validate it with Composer."))
        require = composer.get("require", {}) if isinstance(composer, dict) else {}
        if isinstance(require, dict) and "php" not in require:
            findings.append(_finding("PHP005", "low", "PHP runtime constraint missing", "composer.json", "composer.json does not declare require.php.", "Declare the supported PHP runtime range."))
            checks += 1
    return FrameworkProfile("PHP", True, ("composer.json",) if "composer.json" in files else (), checks), findings


def _go(root: Path, files: set[str]) -> tuple[FrameworkProfile, list[FrameworkFinding]]:
    detected = "go.mod" in files or any(item.endswith(".go") for item in files)
    findings: list[FrameworkFinding] = []
    if not detected:
        return FrameworkProfile("Go", False, (), 0), findings
    checks = 4
    if "go.mod" not in files:
        findings.append(_finding("GO001", "high", "Go module manifest missing", None, "Go source was detected without go.mod.", "Initialize a Go module and pin the intended Go language version."))
    if "go.mod" in files and "go.sum" not in files:
        findings.append(_finding("GO002", "medium", "go.sum missing", None, "go.mod exists but go.sum was not detected.", "Run dependency resolution and commit go.sum for integrity verification."))
    if not any(item.endswith("_test.go") for item in files):
        findings.append(_finding("GO003", "high", "Go tests not detected", None, "No *_test.go files were detected.", "Add table-driven tests, race-sensitive tests, and failure-path coverage."))
    if "go.mod" in files:
        text = _read_text(root, "go.mod")
        if text and not re.search(r"(?m)^go\s+\d+\.\d+", text):
            findings.append(_finding("GO004", "low", "Go version directive missing", "go.mod", "go.mod has no recognizable go version directive.", "Declare the supported Go toolchain version."))
    return FrameworkProfile("Go", True, ("go.mod",) if "go.mod" in files else (), checks), findings


def _rust(root: Path, files: set[str]) -> tuple[FrameworkProfile, list[FrameworkFinding]]:
    detected = "Cargo.toml" in files or any(item.endswith(".rs") for item in files)
    findings: list[FrameworkFinding] = []
    if not detected:
        return FrameworkProfile("Rust", False, (), 0), findings
    checks = 4
    if "Cargo.toml" not in files:
        findings.append(_finding("RS001", "high", "Cargo manifest missing", None, "Rust source was detected without Cargo.toml.", "Create a Cargo package or workspace manifest."))
    if "Cargo.toml" in files and "Cargo.lock" not in files:
        findings.append(_finding("RS002", "medium", "Cargo.lock missing", None, "Cargo.toml exists but Cargo.lock was not detected.", "Commit Cargo.lock for applications and binaries to preserve reproducibility."))
    if not any(item.endswith(".rs") and (item.startswith("tests/") or "/tests/" in item) for item in files) and not any("#[test]" in _read_text(root, item, 300_000) for item in files if item.endswith(".rs")):
        findings.append(_finding("RS003", "high", "Rust tests not detected", None, "No integration tests or #[test] functions were detected.", "Add unit, integration, and failure-path tests."))
    if "Cargo.toml" in files:
        text = _read_text(root, "Cargo.toml")
        if text and not re.search(r"(?m)^rust-version\s*=", text):
            findings.append(_finding("RS004", "low", "Rust version constraint missing", "Cargo.toml", "Cargo.toml does not declare rust-version.", "Declare the minimum supported Rust version and enforce it in CI."))
    return FrameworkProfile("Rust", True, ("Cargo.toml",) if "Cargo.toml" in files else (), checks), findings


ANALYZERS: tuple[Callable[[Path, set[str]], tuple[FrameworkProfile, list[FrameworkFinding]]], ...] = (
    _python,
    _node,
    _android,
    _php,
    _go,
    _rust,
)


def analyze_frameworks(root: Path, files: set[str]) -> tuple[tuple[FrameworkProfile, ...], tuple[FrameworkFinding, ...]]:
    profiles: list[FrameworkProfile] = []
    findings: list[FrameworkFinding] = []
    for analyzer in ANALYZERS:
        profile, analyzer_findings = analyzer(root, files)
        if profile.detected:
            profiles.append(profile)
            findings.extend(analyzer_findings)
    return tuple(profiles), tuple(findings)

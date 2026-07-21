"""Maintainability audit for TStack projects."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".php", ".cs", ".c", ".cpp", ".h", ".hpp"}
IGNORED_DIRS = {".git", ".hg", ".svn", ".tox", ".venv", "venv", "node_modules", "dist", "build", "target", "__pycache__"}


@dataclass(frozen=True)
class ModuleMetric:
    path: str
    lines: int
    severity: str
    recommendation: str


@dataclass(frozen=True)
class MaintainabilityReport:
    schema: str
    root: str
    source_files: int
    test_files: int
    source_lines: int
    test_lines: int
    test_to_source_ratio: float
    oversized_modules: tuple[ModuleMetric, ...]
    verdict: str
    execution_allowed: bool = False


def _iter_source_files(root: Path):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS:
            yield path


def _line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except UnicodeDecodeError:
        return 0


def audit_maintainability(path: Path, *, warn_lines: int = 500, hold_lines: int = 1200) -> MaintainabilityReport:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project directory not found: {root}")

    source_files = test_files = source_lines = test_lines = 0
    oversized: list[ModuleMetric] = []
    for file_path in _iter_source_files(root):
        relative = file_path.relative_to(root).as_posix()
        lines = _line_count(file_path)
        parts = file_path.relative_to(root).parts
        is_test = any(part.lower() in {"test", "tests", "spec", "specs"} for part in parts[:-1]) or file_path.name.startswith("test_")
        if is_test:
            test_files += 1
            test_lines += lines
        else:
            source_files += 1
            source_lines += lines
        if lines >= hold_lines:
            oversized.append(ModuleMetric(relative, lines, "high", "Split into focused modules before adding more behavior."))
        elif lines >= warn_lines:
            oversized.append(ModuleMetric(relative, lines, "medium", "Plan a module boundary and add tests before refactoring."))

    ratio = round(test_lines / source_lines, 4) if source_lines else 0.0
    verdict = "HOLD" if any(item.severity == "high" for item in oversized) else "REVIEW" if oversized or ratio < 0.2 else "PASS"
    return MaintainabilityReport("tstack-maintainability-report/v1", str(root), source_files, test_files, source_lines, test_lines, ratio, tuple(sorted(oversized, key=lambda item: (-item.lines, item.path))), verdict)


def maintainability_json(report: MaintainabilityReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def maintainability_markdown(report: MaintainabilityReport) -> str:
    lines = [
        "# TStack Maintainability Audit",
        "",
        f"- Root: `{report.root}`",
        f"- Source files: {report.source_files}",
        f"- Test files: {report.test_files}",
        f"- Source lines: {report.source_lines}",
        f"- Test lines: {report.test_lines}",
        f"- Test/source ratio: {report.test_to_source_ratio}",
        f"- Verdict: **{report.verdict}**",
        f"- Execution allowed: {'yes' if report.execution_allowed else 'no'}",
        "",
        "## Oversized Modules",
        "",
    ]
    if not report.oversized_modules:
        lines.append("No oversized modules detected.")
    for item in report.oversized_modules:
        lines.extend([f"### [{item.severity.upper()}] `{item.path}`", "", f"- Lines: {item.lines}", f"- Recommendation: {item.recommendation}", ""])
    lines.extend(["## Decision", "", "This audit is report-only. It does not refactor or edit source files.", ""])
    return "\n".join(lines)

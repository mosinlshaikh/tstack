"""Core services for TStack workflow discovery, validation, and project setup."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path

WORKFLOWS = ("architect", "build", "review", "qa", "security", "design", "ship")
REQUIRED_SECTIONS = ("Objective", "Procedure", "Guardrails", "Output")


@dataclass(frozen=True)
class ValidationResult:
    workflow: str
    valid: bool
    missing_sections: tuple[str, ...]
    source: str


def packaged_workflow_path(name: str):
    if name not in WORKFLOWS:
        raise ValueError(f"Unknown workflow: {name}")
    return files("tstack.workflows").joinpath(f"{name}.md")


def load_workflow(name: str) -> str:
    resource = packaged_workflow_path(name)
    if not resource.is_file():
        raise FileNotFoundError(f"Packaged workflow is missing: {name}")
    return resource.read_text(encoding="utf-8")


def validate_workflow(name: str) -> ValidationResult:
    content = load_workflow(name)
    missing = tuple(section for section in REQUIRED_SECTIONS if f"## {section}" not in content)
    return ValidationResult(name, not missing, missing, f"package:tstack.workflows/{name}.md")


def validate_all() -> list[ValidationResult]:
    return [validate_workflow(name) for name in WORKFLOWS]


def initialize_project(destination: Path, *, force: bool = False) -> list[Path]:
    destination = destination.expanduser().resolve()
    tstack_dir = destination / ".tstack"
    workflows_dir = tstack_dir / "workflows"
    generated: list[Path] = []

    if tstack_dir.exists() and not force:
        raise FileExistsError(f"TStack is already initialized at {tstack_dir}; use --force to replace generated files")

    workflows_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "schema_version": 1,
        "policy": {
            "evidence_required": True,
            "critical_conflict_action": "hold",
            "rollback_required_for_release": True,
        },
        "workflows": list(WORKFLOWS),
    }
    config_path = tstack_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generated.append(config_path)

    for name in WORKFLOWS:
        path = workflows_dir / f"{name}.md"
        path.write_text(load_workflow(name), encoding="utf-8")
        generated.append(path)

    gitignore = tstack_dir / ".gitignore"
    gitignore.write_text("reports/\n", encoding="utf-8")
    generated.append(gitignore)
    return generated


def validation_report_json(results: list[ValidationResult]) -> str:
    return json.dumps({"valid": all(item.valid for item in results), "results": [asdict(item) for item in results]}, indent=2)

"""Command-line interface for TStack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tstack import __version__
from tstack.core import WORKFLOWS, initialize_project, load_workflow, validate_all, validation_report_json


def _write_output(content: str, output: str | None) -> None:
    if output is None:
        print(content)
        return
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print(f"Written: {destination}")


def _handle_list(_: argparse.Namespace) -> int:
    for workflow in WORKFLOWS:
        print(workflow)
    return 0


def _handle_workflow(args: argparse.Namespace) -> int:
    _write_output(load_workflow(args.workflow), args.output)
    return 0


def _handle_init(args: argparse.Namespace) -> int:
    generated = initialize_project(Path(args.path), force=args.force)
    print(f"Initialized TStack at {Path(args.path).expanduser().resolve()}")
    for path in generated:
        print(f"  + {path}")
    return 0


def _handle_validate(args: argparse.Namespace) -> int:
    results = validate_all()
    if args.json:
        _write_output(validation_report_json(results), args.output)
    else:
        lines = []
        for result in results:
            status = "PASS" if result.valid else "FAIL"
            detail = "" if result.valid else f" missing={','.join(result.missing_sections)}"
            lines.append(f"{status:4} {result.workflow}{detail}")
        lines.append(f"Verdict: {'PASS' if all(item.valid for item in results) else 'FAIL'}")
        _write_output("\n".join(lines), args.output)
    return 0 if all(item.valid for item in results) else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstack", description="Run TTRL evidence-driven engineering workflows.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available workflows")
    list_parser.set_defaults(handler=_handle_list)

    init_parser = subparsers.add_parser("init", help="Initialize TStack in a project")
    init_parser.add_argument("path", nargs="?", default=".")
    init_parser.add_argument("--force", action="store_true", help="Replace generated TStack files")
    init_parser.set_defaults(handler=_handle_init)

    validate_parser = subparsers.add_parser("validate", help="Validate packaged workflow contracts")
    validate_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    validate_parser.add_argument("--output", "-o")
    validate_parser.set_defaults(handler=_handle_validate)

    for workflow in WORKFLOWS:
        workflow_parser = subparsers.add_parser(workflow, help=f"Print the {workflow} workflow")
        workflow_parser.add_argument("--output", "-o", help="Write the workflow to a file")
        workflow_parser.set_defaults(handler=_handle_workflow, workflow=workflow)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"tstack: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

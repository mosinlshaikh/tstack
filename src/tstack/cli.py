"""Command-line interface for TStack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tstack import __version__

WORKFLOWS = (
    "architect",
    "build",
    "review",
    "qa",
    "security",
    "design",
    "ship",
)


def _repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "commands").is_dir() and (candidate / "pyproject.toml").exists():
            return candidate
    raise FileNotFoundError(
        "TStack repository root not found. Run this command inside a TStack checkout."
    )


def _load_workflow(name: str) -> str:
    path = _repo_root() / "commands" / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Workflow definition is missing: {path}")
    return path.read_text(encoding="utf-8")


def _write_output(content: str, output: str | None) -> None:
    if output is None:
        print(content)
        return

    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print(f"Written: {destination}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tstack",
        description="Run TTRL evidence-driven engineering workflows.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available workflows")
    list_parser.set_defaults(handler=_handle_list)

    for workflow in WORKFLOWS:
        workflow_parser = subparsers.add_parser(
            workflow,
            help=f"Print the {workflow} workflow",
        )
        workflow_parser.add_argument(
            "--output",
            "-o",
            help="Write the workflow to a file instead of stdout",
        )
        workflow_parser.set_defaults(handler=_handle_workflow, workflow=workflow)

    return parser


def _handle_list(_: argparse.Namespace) -> int:
    for workflow in WORKFLOWS:
        print(workflow)
    return 0


def _handle_workflow(args: argparse.Namespace) -> int:
    content = _load_workflow(args.workflow)
    _write_output(content, args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, OSError) as exc:
        print(f"tstack: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

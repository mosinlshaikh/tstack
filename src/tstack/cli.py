"""Command-line interface for TStack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tstack import __version__
from tstack.core import WORKFLOWS, initialize_project, load_workflow, validate_all, validation_report_json
from tstack.policy import (
    baseline_json,
    default_policy_json,
    diff_json,
    diff_markdown,
    diff_report,
    evaluate_policy,
    load_baseline,
    load_policy,
    report_sarif,
)
from tstack.remediation import apply_remediation, remediation_json, remediation_markdown
from tstack.scanner import report_json, report_markdown, scan_project


def _write_output(content: str, output: str | None) -> None:
    if output is None:
        print(content, end="" if content.endswith("\n") else "\n")
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
    policy_path = Path(args.path).expanduser().resolve() / ".tstack" / "policy.json"
    if not policy_path.exists() or args.force:
        policy_path.write_text(default_policy_json(), encoding="utf-8")
        generated.append(policy_path)
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


def _scan(args: argparse.Namespace):
    return scan_project(Path(args.path), max_files=args.max_files, max_file_bytes=args.max_file_bytes)


def _handle_scan(args: argparse.Namespace) -> int:
    report = _scan(args)
    policy = load_policy(Path(args.path).expanduser().resolve(), Path(args.policy).expanduser().resolve() if args.policy else None)
    result = evaluate_policy(report, policy)
    if args.format == "sarif":
        content = report_sarif(report, result.active_findings)
    elif args.format == "json":
        content = report_json(report)
    else:
        content = report_markdown(report)
        content += "\n## Policy Evaluation\n\n"
        content += f"- Verdict: **{'PASS' if result.passed else 'FAIL'}**\n"
        content += f"- Active findings: {len(result.active_findings)}\n"
        content += f"- Suppressed findings: {len(result.suppressed_findings)}\n"
        for reason in result.reasons:
            content += f"- {reason}\n"
    _write_output(content, args.output)
    if args.fail_on == "never":
        return 0
    if not result.passed:
        return 3
    if args.fail_on == "hold":
        return 3 if report.verdict == "HOLD" else 0
    return 3 if report.verdict in {"HOLD", "REVIEW"} else 0


def _handle_baseline(args: argparse.Namespace) -> int:
    report = _scan(args)
    destination = args.output or str(Path(args.path) / ".tstack" / "baseline.json")
    _write_output(baseline_json(report), destination)
    return 0


def _handle_diff(args: argparse.Namespace) -> int:
    report = _scan(args)
    baseline_path = Path(args.baseline).expanduser().resolve()
    diff = diff_report(report, load_baseline(baseline_path))
    content = diff_json(diff) if args.format == "json" else diff_markdown(diff)
    _write_output(content, args.output)
    return 4 if args.fail_on_new and diff.new else 0


def _handle_policy_init(args: argparse.Namespace) -> int:
    destination = Path(args.path).expanduser().resolve() / ".tstack" / "policy.json"
    if destination.exists() and not args.force:
        raise FileExistsError(f"policy already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(default_policy_json(), encoding="utf-8")
    print(f"Written: {destination}")
    return 0


def _handle_fix(args: argparse.Namespace) -> int:
    result = apply_remediation(Path(args.path), dry_run=not args.apply, force=args.force)
    content = remediation_json(result) if args.format == "json" else remediation_markdown(result)
    _write_output(content, args.output)
    return 0


def _add_scan_limits(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--max-files", type=int, default=10000)
    parser.add_argument("--max-file-bytes", type=int, default=1000000)


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

    scan_parser = subparsers.add_parser("scan", help="Audit a project and enforce policy")
    _add_scan_limits(scan_parser)
    scan_parser.add_argument("--format", choices=("markdown", "json", "sarif"), default="markdown")
    scan_parser.add_argument("--output", "-o", help="Write the report to a file")
    scan_parser.add_argument("--policy", help="Explicit policy JSON path")
    scan_parser.add_argument("--fail-on", choices=("never", "hold", "review"), default="hold")
    scan_parser.set_defaults(handler=_handle_scan)

    baseline_parser = subparsers.add_parser("baseline", help="Create a finding baseline from the current project")
    _add_scan_limits(baseline_parser)
    baseline_parser.add_argument("--output", "-o")
    baseline_parser.set_defaults(handler=_handle_baseline)

    diff_parser = subparsers.add_parser("diff", help="Compare current findings with a baseline")
    _add_scan_limits(diff_parser)
    diff_parser.add_argument("--baseline", required=True)
    diff_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    diff_parser.add_argument("--output", "-o")
    diff_parser.add_argument("--fail-on-new", action="store_true")
    diff_parser.set_defaults(handler=_handle_diff)

    policy_parser = subparsers.add_parser("policy-init", help="Create a default project policy")
    policy_parser.add_argument("path", nargs="?", default=".")
    policy_parser.add_argument("--force", action="store_true")
    policy_parser.set_defaults(handler=_handle_policy_init)

    fix_parser = subparsers.add_parser("fix", help="Plan or apply safe missing engineering controls")
    fix_parser.add_argument("path", nargs="?", default=".")
    fix_parser.add_argument("--apply", action="store_true", help="Write planned files; default is dry-run")
    fix_parser.add_argument("--force", action="store_true", help="Allow replacement of files selected by the plan")
    fix_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    fix_parser.add_argument("--output", "-o", help="Write plan/result to a file")
    fix_parser.set_defaults(handler=_handle_fix)

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
    except (FileExistsError, FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"tstack: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

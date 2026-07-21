"""Command-line interface for TStack."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from tstack import __version__
from tstack.container_platform import audit_platform, platform_json, platform_markdown
from tstack.core import WORKFLOWS, initialize_project, load_workflow, validate_all, validation_report_json
from tstack.policy import baseline_json, default_policy_json, diff_json, diff_markdown, diff_report, evaluate_policy, load_baseline, load_policy, report_sarif
from tstack.release_orchestrator import evaluate_release, release_json, release_markdown
from tstack.remediation import apply_remediation, remediation_json, remediation_markdown
from tstack.reproducibility import compare_builds, receipt_json, repro_json, verify_attestation
from tstack.scanner import report_json, report_markdown, scan_project
from tstack.supplychain import build_manifest, checksums_text, manifest_json, sbom_json, verify_manifest
from tstack.trustgate import evaluate_release_trust, trust_gate_json, trust_gate_markdown


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


def _handle_platform_audit(args: argparse.Namespace) -> int:
    report = audit_platform(Path(args.path))
    if args.scope == "docker" and not report.docker_detected:
        raise ValueError("Dockerfile not detected")
    if args.scope == "kubernetes" and not report.kubernetes_detected:
        raise ValueError("Kubernetes manifests not detected")
    filtered = report
    if args.scope != "all":
        prefix = "DOCKER" if args.scope == "docker" else "K8S"
        findings = tuple(item for item in report.findings if item.rule_id.startswith(prefix))
        score = min(100, sum({"critical": 30, "high": 15, "medium": 7, "low": 2}[item.severity] for item in findings))
        verdict = "HOLD" if any(item.severity == "critical" for item in findings) or score >= 60 else "REVIEW" if score >= 20 else "PASS"
        filtered = type(report)(report.root, report.docker_detected, report.kubernetes_detected, report.files_checked, findings, score, verdict)
    _write_output(platform_json(filtered) if args.format == "json" else platform_markdown(filtered), args.output)
    if args.fail_on == "never":
        return 0
    if args.fail_on == "hold":
        return 9 if filtered.verdict == "HOLD" else 0
    return 9 if filtered.verdict in {"HOLD", "REVIEW"} else 0


def _handle_baseline(args: argparse.Namespace) -> int:
    destination = args.output or str(Path(args.path) / ".tstack" / "baseline.json")
    _write_output(baseline_json(_scan(args)), destination)
    return 0


def _handle_diff(args: argparse.Namespace) -> int:
    diff = diff_report(_scan(args), load_baseline(Path(args.baseline).expanduser().resolve()))
    _write_output(diff_json(diff) if args.format == "json" else diff_markdown(diff), args.output)
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
    _write_output(remediation_json(result) if args.format == "json" else remediation_markdown(result), args.output)
    return 0


def _handle_sbom(args: argparse.Namespace) -> int:
    _write_output(sbom_json(), args.output)
    return 0


def _handle_manifest(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    manifest = build_manifest(root)
    _write_output(manifest_json(manifest), args.output or str(root / "manifest.json"))
    if args.checksums:
        _write_output(checksums_text(manifest, "sha256"), str(root / "checksums.sha256"))
        _write_output(checksums_text(manifest, "sha3-256"), str(root / "checksums.sha3-256"))
    return 0


def _handle_verify(args: argparse.Namespace) -> int:
    result = verify_manifest(Path(args.path), Path(args.manifest) if args.manifest else None)
    payload = json.dumps({"valid": result.valid, "checked": result.checked, "missing": result.missing, "mismatched": result.mismatched}, indent=2) + "\n"
    _write_output(payload, args.output)
    return 0 if result.valid else 5


def _handle_repro_verify(args: argparse.Namespace) -> int:
    result = compare_builds(Path(args.original), Path(args.rebuilt))
    _write_output(repro_json(result), args.output)
    return 0 if result.passed else 7


def _handle_attestation_verify(args: argparse.Namespace) -> int:
    receipt = verify_attestation(Path(args.artifact), repository=args.repository, workflow=args.workflow, source_digest=args.source_digest, deny_self_hosted=not args.allow_self_hosted)
    _write_output(receipt_json(receipt), args.output or str(Path(args.artifact).expanduser().resolve().parent / "attestation-verification.json"))
    return 0


def _handle_trust_gate(args: argparse.Namespace) -> int:
    result = evaluate_release_trust(Path(args.path), repository=args.repository, workflow=args.workflow, commit=args.commit, require_attestation_receipt=args.require_attestation_receipt)
    _write_output(trust_gate_json(result) if args.format == "json" else trust_gate_markdown(result), args.output)
    return 0 if result.passed else 6


def _handle_release_check(args: argparse.Namespace) -> int:
    result = evaluate_release(Path(args.project), Path(args.release), Path(args.rebuilt), repository=args.repository, workflow=args.workflow, commit=args.commit, require_attestation_receipt=not args.allow_missing_attestation)
    _write_output(release_json(result) if args.format == "json" else release_markdown(result), args.output)
    return 0 if result.passed else 8


def _add_scan_limits(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--max-files", type=int, default=10000)
    parser.add_argument("--max-file-bytes", type=int, default=1000000)


def _add_platform_parser(subparsers, name: str, scope: str, help_text: str) -> None:
    item = subparsers.add_parser(name, help=help_text)
    item.add_argument("path", nargs="?", default=".")
    item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    item.add_argument("--output", "-o")
    item.add_argument("--fail-on", choices=("never", "hold", "review"), default="hold")
    item.set_defaults(handler=_handle_platform_audit, scope=scope)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tstack", description="Run TTRL evidence-driven engineering workflows.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    item = subparsers.add_parser("list", help="List available workflows"); item.set_defaults(handler=_handle_list)
    item = subparsers.add_parser("init", help="Initialize TStack in a project"); item.add_argument("path", nargs="?", default="."); item.add_argument("--force", action="store_true"); item.set_defaults(handler=_handle_init)
    item = subparsers.add_parser("validate", help="Validate packaged workflow contracts"); item.add_argument("--json", action="store_true"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_validate)
    item = subparsers.add_parser("scan", help="Audit a project and enforce policy"); _add_scan_limits(item); item.add_argument("--format", choices=("markdown", "json", "sarif"), default="markdown"); item.add_argument("--output", "-o"); item.add_argument("--policy"); item.add_argument("--fail-on", choices=("never", "hold", "review"), default="hold"); item.set_defaults(handler=_handle_scan)
    _add_platform_parser(subparsers, "platform-audit", "all", "Audit Docker and Kubernetes security controls")
    _add_platform_parser(subparsers, "docker-audit", "docker", "Audit Dockerfile security and reproducibility")
    _add_platform_parser(subparsers, "k8s-audit", "kubernetes", "Audit Kubernetes workload security and resilience")
    item = subparsers.add_parser("baseline", help="Create a finding baseline"); _add_scan_limits(item); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_baseline)
    item = subparsers.add_parser("diff", help="Compare current findings with a baseline"); _add_scan_limits(item); item.add_argument("--baseline", required=True); item.add_argument("--format", choices=("markdown", "json"), default="markdown"); item.add_argument("--output", "-o"); item.add_argument("--fail-on-new", action="store_true"); item.set_defaults(handler=_handle_diff)
    item = subparsers.add_parser("policy-init", help="Create a default project policy"); item.add_argument("path", nargs="?", default="."); item.add_argument("--force", action="store_true"); item.set_defaults(handler=_handle_policy_init)
    item = subparsers.add_parser("fix", help="Plan or apply safe controls"); item.add_argument("path", nargs="?", default="."); item.add_argument("--apply", action="store_true"); item.add_argument("--force", action="store_true"); item.add_argument("--format", choices=("markdown", "json"), default="markdown"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_fix)
    item = subparsers.add_parser("sbom", help="Generate CycloneDX JSON SBOM for the active environment"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_sbom)
    item = subparsers.add_parser("manifest", help="Create deterministic dual-hash release artifact manifest"); item.add_argument("path", nargs="?", default="dist"); item.add_argument("--output", "-o"); item.add_argument("--checksums", action="store_true"); item.set_defaults(handler=_handle_manifest)
    item = subparsers.add_parser("verify", help="Verify artifacts against a release manifest"); item.add_argument("path", nargs="?", default="dist"); item.add_argument("--manifest"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_verify)
    item = subparsers.add_parser("repro-verify", help="Compare official and independently rebuilt artifacts"); item.add_argument("original"); item.add_argument("rebuilt"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_repro_verify)
    item = subparsers.add_parser("attestation-verify", help="Verify GitHub/Sigstore provenance and write a receipt"); item.add_argument("artifact"); item.add_argument("--repository", required=True); item.add_argument("--workflow", default=".github/workflows/release.yml"); item.add_argument("--source-digest"); item.add_argument("--allow-self-hosted", action="store_true"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_attestation_verify)
    item = subparsers.add_parser("trust-gate", help="Evaluate complete release integrity and provenance prerequisites"); item.add_argument("path", nargs="?", default="dist"); item.add_argument("--repository", required=True); item.add_argument("--workflow", default=".github/workflows/release.yml"); item.add_argument("--commit", required=True); item.add_argument("--require-attestation-receipt", action="store_true"); item.add_argument("--format", choices=("markdown", "json"), default="markdown"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_trust_gate)
    item = subparsers.add_parser("release-check", help="Run the complete project, artifact, reproducibility, and provenance release gate"); item.add_argument("--project", default="."); item.add_argument("--release", default="dist"); item.add_argument("--rebuilt", required=True); item.add_argument("--repository", required=True); item.add_argument("--workflow", default=".github/workflows/release.yml"); item.add_argument("--commit", required=True); item.add_argument("--allow-missing-attestation", action="store_true"); item.add_argument("--format", choices=("markdown", "json"), default="markdown"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_release_check)
    for workflow in WORKFLOWS:
        item = subparsers.add_parser(workflow, help=f"Print the {workflow} workflow"); item.add_argument("--output", "-o"); item.set_defaults(handler=_handle_workflow, workflow=workflow)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser(); args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileExistsError, FileNotFoundError, OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"tstack: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

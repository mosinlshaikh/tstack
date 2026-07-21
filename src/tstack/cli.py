"""Command-line interface for TStack."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from tstack import __version__
from tstack.agentic import agent_catalog_json, agent_catalog_markdown, agent_plan_json, agent_plan_markdown, agent_selection_json, agent_selection_markdown, agent_stats, agent_stats_json, agent_stats_markdown, build_agent_plan, build_orchestration_plan, failure_route_json, failure_route_markdown, get_agent, list_agents, orchestration_json, orchestration_markdown, route_failure, select_agents_for_goal
from tstack.approval import approval_decision_json, approval_decision_markdown, approval_readiness_json, approval_readiness_markdown, approval_request_json, approval_request_markdown, create_approval_request, decide_approval, evaluate_readiness
from tstack.automation import get_capability, list_capabilities, registry_json, registry_markdown, validate_automation, validation_json as automation_validation_json, validation_markdown as automation_validation_markdown
from tstack.container_platform import audit_platform, platform_json, platform_markdown
from tstack.core import WORKFLOWS, initialize_project, load_workflow, validate_all, validation_report_json
from tstack.executor import execution_plan_json as executor_plan_json, execution_plan_markdown as executor_plan_markdown, plan_execution
from tstack.human_language import HumanExecutionPlan, execution_plan_json as human_execution_plan_json, execution_plan_markdown as human_execution_plan_markdown, human_languages_json, human_languages_markdown, intent_json, intent_markdown, parse_intent
from tstack.knowledge import get_pack, knowledge_stats, list_packs, pack_json, pack_markdown, packs_json, packs_markdown, read_topic, search_json, search_knowledge, search_markdown, stats_json, stats_markdown, validate_knowledge, validation_json, validation_markdown
from tstack.policy import baseline_json, default_policy_json, diff_json, diff_markdown, diff_report, evaluate_policy, load_baseline, load_policy, report_sarif
from tstack.release_orchestrator import evaluate_release, release_json, release_markdown
from tstack.remediation import apply_remediation, remediation_json, remediation_markdown
from tstack.reproducibility import compare_builds, receipt_json, repro_json, verify_attestation
from tstack.scanner import report_json, report_markdown, scan_project
from tstack.ssh import create_ssh_policy, load_ssh_policy, plan_ssh_command, ssh_plan_json, ssh_plan_markdown
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


def _handle_knowledge(args: argparse.Namespace) -> int:
    if args.knowledge_command == "list":
        packs = list_packs()
        _write_output(packs_json(packs) if args.format == "json" else packs_markdown(packs), args.output)
        return 0
    if args.knowledge_command == "show":
        pack = get_pack(args.pack_id)
        _write_output(pack_json(pack) if args.format == "json" else pack_markdown(pack), args.output)
        return 0
    if args.knowledge_command == "validate":
        result = validate_knowledge()
        _write_output(validation_json(result) if args.format == "json" else validation_markdown(result), args.output)
        return 0 if result.valid else 12
    if args.knowledge_command == "stats":
        stats = knowledge_stats()
        _write_output(stats_json(stats) if args.format == "json" else stats_markdown(stats), args.output)
        return 0
    if args.knowledge_command == "topic":
        _write_output(read_topic(args.pack_id, args.topic_id), args.output)
        return 0
    if args.knowledge_command == "search":
        hits = search_knowledge(args.query, limit=args.limit)
        _write_output(search_json(args.query, hits) if args.format == "json" else search_markdown(args.query, hits), args.output)
        return 0
    raise ValueError(f"unknown knowledge command: {args.knowledge_command}")


def _handle_automation(args: argparse.Namespace) -> int:
    if args.automation_command == "list":
        capabilities = list_capabilities()
        _write_output(registry_json(capabilities) if args.format == "json" else registry_markdown(capabilities), args.output)
        return 0
    if args.automation_command == "show":
        capability = get_capability(args.capability_id)
        _write_output(registry_json((capability,)) if args.format == "json" else registry_markdown((capability,)), args.output)
        return 0
    if args.automation_command == "validate":
        result = validate_automation()
        _write_output(automation_validation_json(result) if args.format == "json" else automation_validation_markdown(result), args.output)
        return 0 if result.valid else 14
    raise ValueError(f"unknown automation command: {args.automation_command}")


def _handle_agent(args: argparse.Namespace) -> int:
    if args.agent_command == "plan":
        plan = build_agent_plan(args.goal, include_uiux=not args.no_uiux, include_deployment=not args.no_deployment)
        _write_output(agent_plan_json(plan) if args.format == "json" else agent_plan_markdown(plan), args.output)
        return 0
    if args.agent_command == "catalog":
        agents = list_agents(args.category)
        _write_output(agent_catalog_json(agents) if args.format == "json" else agent_catalog_markdown(agents), args.output)
        return 0
    if args.agent_command == "show":
        agent = get_agent(args.agent_id)
        _write_output(agent_catalog_json((agent,)) if args.format == "json" else agent_catalog_markdown((agent,)), args.output)
        return 0
    if args.agent_command == "select":
        selection = select_agents_for_goal(args.goal)
        _write_output(agent_selection_json(selection) if args.format == "json" else agent_selection_markdown(selection), args.output)
        return 0
    if args.agent_command == "orchestrate":
        plan = build_orchestration_plan(args.goal)
        _write_output(orchestration_json(plan) if args.format == "json" else orchestration_markdown(plan), args.output)
        return 0
    if args.agent_command == "stats":
        stats = agent_stats()
        _write_output(agent_stats_json(stats) if args.format == "json" else agent_stats_markdown(stats), args.output)
        return 0
    if args.agent_command == "route-failure":
        route = route_failure(args.description, failure_type=args.type)
        _write_output(failure_route_json(route) if args.format == "json" else failure_route_markdown(route), args.output)
        return 0
    raise ValueError(f"unknown agent command: {args.agent_command}")


def _handle_approval(args: argparse.Namespace) -> int:
    if args.approval_command == "request":
        request = create_approval_request(args.action, request_id=args.request_id)
        _write_output(approval_request_json(request) if args.format == "json" else approval_request_markdown(request), args.output)
        return 0
    if args.approval_command == "decide":
        decision = decide_approval(Path(args.request), approved=args.approved, approver=args.approver, reason=args.reason)
        _write_output(approval_decision_json(decision) if args.format == "json" else approval_decision_markdown(decision), args.output)
        return 0
    if args.approval_command == "readiness":
        readiness = evaluate_readiness(Path(args.request), Path(args.decision))
        _write_output(approval_readiness_json(readiness) if args.format == "json" else approval_readiness_markdown(readiness), args.output)
        return 0
    raise ValueError(f"unknown approval command: {args.approval_command}")


def _handle_execute(args: argparse.Namespace) -> int:
    if args.execute_command == "plan":
        plan = plan_execution(Path(args.request), Path(args.decision), target=Path(args.target) if args.target else None, apply=args.apply)
        _write_output(executor_plan_json(plan) if args.format == "json" else executor_plan_markdown(plan), args.output)
        return 0 if plan.executable else 15
    raise ValueError(f"unknown execute command: {args.execute_command}")


def _handle_human(args: argparse.Namespace) -> int:
    if args.human_command == "languages":
        _write_output(human_languages_json() if args.format == "json" else human_languages_markdown(), args.output)
        return 0
    if args.human_command == "intent":
        parsed = parse_intent(args.text)
        _write_output(intent_json(parsed) if args.format == "json" else intent_markdown(parsed), args.output)
        return 0
    if args.human_command == "run":
        parsed = parse_intent(args.text)
        routed_plan = None
        routed = False
        route = "clarify"
        if parsed.intent == "agent_plan":
            routed = True
            route = "agent.plan"
            routed_plan = json.loads(agent_plan_json(build_agent_plan(parsed.text)))
        elif parsed.intent == "knowledge_search":
            routed = True
            route = "knowledge.search"
        elif parsed.intent == "scan":
            routed = True
            route = "scan"
        elif parsed.intent == "fix_plan":
            routed = True
            route = "fix.plan"
        elif parsed.intent == "ssh_plan":
            routed = True
            route = "ssh.plan"
        plan = HumanExecutionPlan(
            schema="tstack-human-execution-plan/v1",
            intent=parsed,
            routed=routed,
            route=route,
            execution_allowed=False,
            approval_required=True,
            plan=routed_plan,
            notes=(
                "Human run mode routes intent into a safe plan only.",
                "No command is executed automatically.",
                "A future approval engine may execute selected low-risk steps after explicit approval.",
            ),
        )
        _write_output(human_execution_plan_json(plan) if args.format == "json" else human_execution_plan_markdown(plan), args.output)
        return 0
    raise ValueError(f"unknown human command: {args.human_command}")


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


def _handle_ssh(args: argparse.Namespace) -> int:
    if args.ssh_command == "init":
        destination = create_ssh_policy(Path(args.path), force=args.force)
        print(f"Written: {destination}")
        return 0
    if args.ssh_command == "plan":
        policy = load_ssh_policy(Path(args.policy).expanduser().resolve())
        plan = plan_ssh_command(policy, target=args.target, command=args.remote_command, user=args.user, port=args.port)
        _write_output(ssh_plan_json(plan) if args.format == "json" else ssh_plan_markdown(plan), args.output)
        return 0 if plan.valid else 13
    raise ValueError(f"unknown ssh command: {args.ssh_command}")


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
    item = subparsers.add_parser("knowledge", help="Inspect registered engineering knowledge packs")
    knowledge_subparsers = item.add_subparsers(dest="knowledge_command", required=True)
    knowledge_item = knowledge_subparsers.add_parser("list", help="List registered knowledge packs")
    knowledge_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    knowledge_item.add_argument("--output", "-o")
    knowledge_item.set_defaults(handler=_handle_knowledge)
    knowledge_item = knowledge_subparsers.add_parser("show", help="Show a registered knowledge pack summary")
    knowledge_item.add_argument("pack_id")
    knowledge_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    knowledge_item.add_argument("--output", "-o")
    knowledge_item.set_defaults(handler=_handle_knowledge)
    knowledge_item = knowledge_subparsers.add_parser("validate", help="Validate registered knowledge pack contracts")
    knowledge_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    knowledge_item.add_argument("--output", "-o")
    knowledge_item.set_defaults(handler=_handle_knowledge)
    knowledge_item = knowledge_subparsers.add_parser("stats", help="Show knowledge pack counts and coverage")
    knowledge_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    knowledge_item.add_argument("--output", "-o")
    knowledge_item.set_defaults(handler=_handle_knowledge)
    knowledge_item = knowledge_subparsers.add_parser("topic", help="Print one topic from a knowledge pack")
    knowledge_item.add_argument("pack_id")
    knowledge_item.add_argument("topic_id")
    knowledge_item.add_argument("--output", "-o")
    knowledge_item.set_defaults(handler=_handle_knowledge)
    knowledge_item = knowledge_subparsers.add_parser("search", help="Search knowledge pack topic content")
    knowledge_item.add_argument("query")
    knowledge_item.add_argument("--limit", type=int, default=20)
    knowledge_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    knowledge_item.add_argument("--output", "-o")
    knowledge_item.set_defaults(handler=_handle_knowledge)
    item = subparsers.add_parser("automation", help="Inspect TStack automation and plugin safety capabilities")
    automation_subparsers = item.add_subparsers(dest="automation_command", required=True)
    automation_item = automation_subparsers.add_parser("list", help="List registered automation capabilities")
    automation_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    automation_item.add_argument("--output", "-o")
    automation_item.set_defaults(handler=_handle_automation)
    automation_item = automation_subparsers.add_parser("show", help="Show one automation capability")
    automation_item.add_argument("capability_id")
    automation_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    automation_item.add_argument("--output", "-o")
    automation_item.set_defaults(handler=_handle_automation)
    automation_item = automation_subparsers.add_parser("validate", help="Validate automation safety registry")
    automation_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    automation_item.add_argument("--output", "-o")
    automation_item.set_defaults(handler=_handle_automation)
    item = subparsers.add_parser("agent", help="Plan approval-gated agentic delivery from discovery to deployment")
    agent_subparsers = item.add_subparsers(dest="agent_command", required=True)
    agent_item = agent_subparsers.add_parser("plan", help="Create a plan-only agentic delivery workflow")
    agent_item.add_argument("goal")
    agent_item.add_argument("--no-uiux", action="store_true")
    agent_item.add_argument("--no-deployment", action="store_true")
    agent_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    agent_item.add_argument("--output", "-o")
    agent_item.set_defaults(handler=_handle_agent)
    agent_item = agent_subparsers.add_parser("orchestrate", help="Map selected agents into delivery phases")
    agent_item.add_argument("goal")
    agent_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    agent_item.add_argument("--output", "-o")
    agent_item.set_defaults(handler=_handle_agent)
    agent_item = agent_subparsers.add_parser("select", help="Select relevant agents for a goal")
    agent_item.add_argument("goal")
    agent_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    agent_item.add_argument("--output", "-o")
    agent_item.set_defaults(handler=_handle_agent)
    agent_item = agent_subparsers.add_parser("stats", help="Show specialized agent category and safety counts")
    agent_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    agent_item.add_argument("--output", "-o")
    agent_item.set_defaults(handler=_handle_agent)
    agent_item = agent_subparsers.add_parser("route-failure", help="Route a test, CI, security, performance, or UI failure to the right agent")
    agent_item.add_argument("description")
    agent_item.add_argument("--type", choices=("auto", "test", "security", "performance", "devops", "uiux", "general"), default="auto")
    agent_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    agent_item.add_argument("--output", "-o")
    agent_item.set_defaults(handler=_handle_agent)
    agent_item = agent_subparsers.add_parser("catalog", help="List specialized TStack agents")
    agent_item.add_argument("--category")
    agent_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    agent_item.add_argument("--output", "-o")
    agent_item.set_defaults(handler=_handle_agent)
    agent_item = agent_subparsers.add_parser("show", help="Show one specialized TStack agent")
    agent_item.add_argument("agent_id")
    agent_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    agent_item.add_argument("--output", "-o")
    agent_item.set_defaults(handler=_handle_agent)
    item = subparsers.add_parser("approval", help="Create and record approval-gated execution decisions")
    approval_subparsers = item.add_subparsers(dest="approval_command", required=True)
    approval_item = approval_subparsers.add_parser("request", help="Create an approval request for a proposed action")
    approval_item.add_argument("action")
    approval_item.add_argument("--request-id", default="APPROVAL-0001")
    approval_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    approval_item.add_argument("--output", "-o")
    approval_item.set_defaults(handler=_handle_approval)
    approval_item = approval_subparsers.add_parser("decide", help="Record a human approval or rejection for a request")
    approval_item.add_argument("request")
    approval_item.add_argument("--approved", action="store_true")
    approval_item.add_argument("--approver", required=True)
    approval_item.add_argument("--reason", required=True)
    approval_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    approval_item.add_argument("--output", "-o")
    approval_item.set_defaults(handler=_handle_approval)
    approval_item = approval_subparsers.add_parser("readiness", help="Evaluate whether an approved request is ready for future execution")
    approval_item.add_argument("request")
    approval_item.add_argument("decision")
    approval_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    approval_item.add_argument("--output", "-o")
    approval_item.set_defaults(handler=_handle_approval)
    item = subparsers.add_parser("execute", help="Plan controlled execution for approved low-risk actions")
    execute_subparsers = item.add_subparsers(dest="execute_command", required=True)
    execute_item = execute_subparsers.add_parser("plan", help="Create a dry-run execution plan from approval files")
    execute_item.add_argument("request")
    execute_item.add_argument("decision")
    execute_item.add_argument("--target")
    execute_item.add_argument("--apply", action="store_true")
    execute_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    execute_item.add_argument("--output", "-o")
    execute_item.set_defaults(handler=_handle_execute)
    item = subparsers.add_parser("human", help="Parse human language and typo-tolerant user intent")
    human_subparsers = item.add_subparsers(dest="human_command", required=True)
    human_item = human_subparsers.add_parser("languages", help="List supported human language registry")
    human_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    human_item.add_argument("--output", "-o")
    human_item.set_defaults(handler=_handle_human)
    human_item = human_subparsers.add_parser("intent", help="Parse typo-tolerant human instruction into a safe command suggestion")
    human_item.add_argument("text")
    human_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    human_item.add_argument("--output", "-o")
    human_item.set_defaults(handler=_handle_human)
    human_item = human_subparsers.add_parser("run", help="Parse human instruction and route it into a safe execution plan")
    human_item.add_argument("text")
    human_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    human_item.add_argument("--output", "-o")
    human_item.set_defaults(handler=_handle_human)
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
    item = subparsers.add_parser("ssh", help="Plan policy-controlled SSH automation without remote execution")
    ssh_subparsers = item.add_subparsers(dest="ssh_command", required=True)
    ssh_item = ssh_subparsers.add_parser("init", help="Create a default SSH automation policy")
    ssh_item.add_argument("path", nargs="?", default=".")
    ssh_item.add_argument("--force", action="store_true")
    ssh_item.set_defaults(handler=_handle_ssh)
    ssh_item = ssh_subparsers.add_parser("plan", help="Create a policy-checked SSH command plan")
    ssh_item.add_argument("target")
    ssh_item.add_argument("remote_command")
    ssh_item.add_argument("--policy", required=True)
    ssh_item.add_argument("--user")
    ssh_item.add_argument("--port", type=int)
    ssh_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    ssh_item.add_argument("--output", "-o")
    ssh_item.set_defaults(handler=_handle_ssh)
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

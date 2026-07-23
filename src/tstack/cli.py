"""Command-line interface for TStack."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from tstack import __version__
from tstack.agentic import agent_catalog_json, agent_catalog_markdown, agent_plan_json, agent_plan_markdown, agent_selection_json, agent_selection_markdown, agent_stats, agent_stats_json, agent_stats_markdown, build_agent_plan, build_orchestration_plan, failure_route_json, failure_route_markdown, get_agent, list_agents, orchestration_json, orchestration_markdown, route_failure, select_agents_for_goal
from tstack.approval import approval_decision_json, approval_decision_markdown, approval_readiness_json, approval_readiness_markdown, approval_request_json, approval_request_markdown, create_approval_request, decide_approval, evaluate_readiness
from tstack.audit_log import append_audit_event, audit_log_json, audit_log_markdown, verify_audit_log
from tstack.automation import get_capability, list_capabilities, registry_json, registry_markdown, validate_automation, validation_json as automation_validation_json, validation_markdown as automation_validation_markdown
from tstack.bug import bug_report_json, bug_report_markdown, find_bugs
from tstack.capabilities import capability_registry_json, capability_registry_markdown, capability_validation_json, get_capability_definition, list_capability_definitions, validate_capability_registry
from tstack.container_platform import audit_platform, platform_json, platform_markdown
from tstack.core import WORKFLOWS, initialize_project, load_workflow, validate_all, validation_report_json
from tstack.creation import create_plan, creation_blueprint_json, creation_blueprint_markdown, creation_plan_json, creation_plan_markdown
from tstack.desktop import desktop_blueprint_json, desktop_blueprint_markdown
from tstack.executor import apply_execution, execution_plan_json as executor_plan_json, execution_plan_markdown as executor_plan_markdown, execution_result_json, execution_result_markdown, plan_execution
from tstack.environment import environment_json, environment_markdown, inspect_environment
from tstack.file_agent import build_inventory, inventory_json, inventory_markdown, organize_plan_json, organize_plan_markdown, plan_organize
from tstack.file_runtime import apply_file_transaction, file_transaction_json, file_transaction_markdown, undo_file_transaction
from tstack.human_language import HumanExecutionPlan, execution_plan_json as human_execution_plan_json, execution_plan_markdown as human_execution_plan_markdown, human_languages_json, human_languages_markdown, intent_json, intent_markdown, parse_intent
from tstack.kernel import approve_task, benchmark_worker_run, cancel_task as kernel_cancel_task, daemon_status, enqueue_task, export_workspace_state, get_task, import_workspace_state, init_workspace as kernel_init_workspace, kernel_json, list_events as kernel_list_events, list_tasks as kernel_list_tasks, recover_stuck_tasks, retry_task, revoke_approval, rollback_task, run_daemon, run_next_task, run_task, run_worker_pool, start_daemon_foundation, submit_task, verify_audit_chain
from tstack.knowledge import get_pack, knowledge_stats, list_packs, pack_json, pack_markdown, packs_json, packs_markdown, read_topic, search_json, search_knowledge, search_markdown, stats_json, stats_markdown, validate_knowledge, validation_json, validation_markdown
from tstack.maintainability import audit_maintainability, maintainability_json, maintainability_markdown
from tstack.mastery import level_10_mastery_profile, mastery_json, mastery_markdown
from tstack.policy import baseline_json, default_policy_json, diff_json, diff_markdown, diff_report, evaluate_policy, load_baseline, load_policy, report_sarif
from tstack.release_orchestrator import evaluate_release, release_json, release_markdown
from tstack.remediation import apply_remediation, remediation_json, remediation_markdown
from tstack.reproducibility import compare_builds, receipt_json, repro_json, verify_attestation
from tstack.runtime import approve_runtime_request, create_audit_event, create_process_run_request, create_runtime_request, runtime_json, runtime_markdown
from tstack.sandbox import default_sandbox_policy, load_sandbox_policy, plan_sandbox_command, run_sandbox_command, sandbox_plan_json, sandbox_plan_markdown, sandbox_policy_json, sandbox_result_json, sandbox_result_markdown
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


def _handle_capability(args: argparse.Namespace) -> int:
    if args.capability_command == "list":
        capabilities = list_capability_definitions(args.status)
        _write_output(capability_registry_json(capabilities) if args.format == "json" else capability_registry_markdown(capabilities), args.output)
        return 0
    if args.capability_command == "show":
        capability = get_capability_definition(args.capability_id)
        _write_output(capability_registry_json((capability,)) if args.format == "json" else capability_registry_markdown((capability,)), args.output)
        return 0
    if args.capability_command == "validate":
        errors = validate_capability_registry()
        _write_output(capability_validation_json(errors), args.output)
        return 0 if not errors else 25
    raise ValueError(f"unknown capability command: {args.capability_command}")


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
        if args.apply:
            if not args.target:
                raise ValueError("execute plan --apply requires --target")
            result = apply_execution(Path(args.request), Path(args.decision), target=Path(args.target))
            _write_output(execution_result_json(result) if args.format == "json" else execution_result_markdown(result), args.output)
            return 0
        plan = plan_execution(Path(args.request), Path(args.decision), target=Path(args.target) if args.target else None, apply=args.apply)
        _write_output(executor_plan_json(plan) if args.format == "json" else executor_plan_markdown(plan), args.output)
        return 0 if plan.executable else 15
    raise ValueError(f"unknown execute command: {args.execute_command}")


def _handle_runtime(args: argparse.Namespace) -> int:
    if args.runtime_command == "request":
        if args.capability == "process.run" and args.command:
            request = create_process_run_request(args.intent, tuple(args.command), target=args.target, request_id=args.request_id, cwd=args.cwd, write=args.write, network=args.network, timeout_seconds=args.timeout_seconds)
        elif args.capability == "process.run":
            raise ValueError("process.run runtime request requires --cmd so approval binds the exact command")
        else:
            request = create_runtime_request(args.capability, args.intent, target=args.target, request_id=args.request_id)
        _write_output(runtime_json(request) if args.format == "json" else runtime_markdown(request), args.output)
        return 0
    if args.runtime_command == "decide":
        decision = approve_runtime_request(Path(args.request), approved=args.approved, approver=args.approver, reason=args.reason)
        _write_output(runtime_json(decision) if args.format == "json" else runtime_markdown(decision), args.output)
        return 0
    if args.runtime_command == "audit":
        event = create_audit_event(Path(args.request), Path(args.decision) if args.decision else None, outcome=args.outcome)
        _write_output(runtime_json(event) if args.format == "json" else runtime_markdown(event), args.output)
        return 0
    raise ValueError(f"unknown runtime command: {args.runtime_command}")


def _handle_audit_log(args: argparse.Namespace) -> int:
    if args.audit_log_command == "append":
        entry = append_audit_event(Path(args.log), Path(args.event))
        _write_output(audit_log_json(entry) if args.format == "json" else audit_log_markdown(entry), args.output)
        return 0
    if args.audit_log_command == "verify":
        result = verify_audit_log(Path(args.log))
        _write_output(audit_log_json(result) if args.format == "json" else audit_log_markdown(result), args.output)
        return 0 if result.valid else 18
    raise ValueError(f"unknown audit-log command: {args.audit_log_command}")


def _handle_sandbox(args: argparse.Namespace) -> int:
    if args.sandbox_command == "init":
        policy = default_sandbox_policy(Path(args.workspace))
        _write_output(sandbox_policy_json(policy), args.output)
        return 0
    if args.sandbox_command == "plan":
        policy = load_sandbox_policy(Path(args.policy))
        command = tuple(part for part in args.command if part != "--")
        plan = plan_sandbox_command(policy, command, cwd=Path(args.cwd) if args.cwd else None, write=args.write, network=args.network)
        _write_output(sandbox_plan_json(plan) if args.format == "json" else sandbox_plan_markdown(plan), args.output)
        return 0 if not plan.blockers else 19
    if args.sandbox_command == "run":
        policy = load_sandbox_policy(Path(args.policy))
        command = tuple(part for part in args.command if part != "--")
        result = run_sandbox_command(policy, command, cwd=Path(args.cwd) if args.cwd else None, write=args.write, network=args.network, request_path=Path(args.request), decision_path=Path(args.decision))
        _write_output(sandbox_result_json(result) if args.format == "json" else sandbox_result_markdown(result), args.output)
        return 0 if result.executed and result.exit_code == 0 and not result.timed_out else 20
    raise ValueError(f"unknown sandbox command: {args.sandbox_command}")


def _handle_workspace(args: argparse.Namespace) -> int:
    if args.workspace_command == "init":
        workspace = kernel_init_workspace(Path(args.path))
        _write_output(kernel_json(workspace), args.output)
        return 0
    if args.workspace_command == "export":
        bundle = export_workspace_state(Path(args.workspace))
        _write_output(kernel_json(bundle), args.output)
        return 0
    if args.workspace_command == "import":
        workspace = import_workspace_state(Path(args.workspace), Path(args.bundle))
        _write_output(kernel_json(workspace), args.output)
        return 0
    raise ValueError(f"unknown workspace command: {args.workspace_command}")


def _handle_daemon(args: argparse.Namespace) -> int:
    if args.daemon_command == "start":
        status = start_daemon_foundation(Path(args.workspace))
        _write_output(kernel_json(status), args.output)
        return 0
    if args.daemon_command == "status":
        status = daemon_status(Path(args.workspace))
        _write_output(kernel_json(status), args.output)
        return 0 if status.database_exists and status.audit_chain_valid else 23
    if args.daemon_command == "recover":
        result = recover_stuck_tasks(Path(args.workspace), policy=args.policy)
        _write_output(kernel_json(result), args.output)
        return 0
    if args.daemon_command == "run":
        result = run_daemon(Path(args.workspace), daemon_id=args.daemon_id, cycles=args.cycles, interval_seconds=args.interval_seconds, worker_limit=args.worker_limit, recovery_policy=args.recovery_policy)
        _write_output(kernel_json(result), args.output)
        return 0 if result.audit_chain_valid and result.failed == 0 else 24
    raise ValueError(f"unknown daemon command: {args.daemon_command}")


def _handle_task(args: argparse.Namespace) -> int:
    if args.task_command == "submit":
        task = submit_task(Path(args.workspace), capability=args.capability, target=args.target, content=args.content)
        _write_output(kernel_json(task), args.output)
        return 0
    if args.task_command == "list":
        _write_output(kernel_json(kernel_list_tasks(Path(args.workspace))), args.output)
        return 0
    if args.task_command == "show":
        _write_output(kernel_json(get_task(Path(args.workspace), args.task_id)), args.output)
        return 0
    if args.task_command == "run":
        result = run_task(Path(args.workspace), args.task_id, timeout_seconds=args.timeout_seconds)
        _write_output(kernel_json(result), args.output)
        return 0
    if args.task_command == "queue":
        _write_output(kernel_json(enqueue_task(Path(args.workspace), args.task_id)), args.output)
        return 0
    if args.task_command == "run-next":
        result = run_next_task(Path(args.workspace), timeout_seconds=args.timeout_seconds)
        _write_output(kernel_json(result), args.output)
        return 0 if result.state == "SUCCEEDED" else 22
    if args.task_command == "events":
        _write_output(kernel_json(kernel_list_events(Path(args.workspace), args.task_id)), args.output)
        return 0
    if args.task_command == "cancel":
        _write_output(kernel_json(kernel_cancel_task(Path(args.workspace), args.task_id, reason=args.reason)), args.output)
        return 0
    if args.task_command == "retry":
        _write_output(kernel_json(retry_task(Path(args.workspace), args.task_id, reason=args.reason)), args.output)
        return 0
    raise ValueError(f"unknown task command: {args.task_command}")


def _handle_kernel_approval(args: argparse.Namespace) -> int:
    if args.kernel_approval_command == "approve":
        approval = approve_task(Path(args.workspace), args.task_id, actor=args.actor, mode=args.mode, expires_at=args.expires_at, max_uses=args.max_uses)
        _write_output(kernel_json(approval), args.output)
        return 0
    if args.kernel_approval_command == "revoke":
        revocation = revoke_approval(Path(args.workspace), args.approval_id, actor=args.actor, reason=args.reason)
        _write_output(kernel_json(revocation), args.output)
        return 0
    raise ValueError(f"unknown kernel approval command: {args.kernel_approval_command}")


def _handle_kernel_rollback(args: argparse.Namespace) -> int:
    if args.kernel_rollback_command == "apply":
        result = rollback_task(Path(args.workspace), args.task_id)
        _write_output(kernel_json(result), args.output)
        return 0
    raise ValueError(f"unknown kernel rollback command: {args.kernel_rollback_command}")


def _handle_kernel_audit(args: argparse.Namespace) -> int:
    if args.kernel_audit_command == "verify":
        valid = verify_audit_chain(Path(args.workspace))
        _write_output(json.dumps({"schema": "tstack-kernel-audit-verification/v1", "valid": valid}, indent=2, sort_keys=True) + "\n", args.output)
        return 0 if valid else 21
    raise ValueError(f"unknown kernel audit command: {args.kernel_audit_command}")


def _handle_worker(args: argparse.Namespace) -> int:
    if args.worker_command == "run":
        result = run_worker_pool(Path(args.workspace), workers=args.workers, limit=args.limit, timeout_seconds=args.timeout_seconds)
        _write_output(kernel_json(result), args.output)
        return 0 if result.failed == 0 else 24
    raise ValueError(f"unknown worker command: {args.worker_command}")


def _handle_benchmark(args: argparse.Namespace) -> int:
    if args.benchmark_command == "kernel":
        result = benchmark_worker_run(Path(args.workspace), tasks=args.tasks, workers=args.workers)
        _write_output(kernel_json(result), args.output)
        return 0 if result.failed == 0 and result.audit_chain_valid else 26
    raise ValueError(f"unknown benchmark command: {args.benchmark_command}")


def _handle_desktop(args: argparse.Namespace) -> int:
    if args.desktop_command == "blueprint":
        _write_output(desktop_blueprint_json() if args.format == "json" else desktop_blueprint_markdown(), args.output)
        return 0
    raise ValueError(f"unknown desktop command: {args.desktop_command}")


def _handle_creation(args: argparse.Namespace) -> int:
    if args.creation_command == "blueprint":
        _write_output(creation_blueprint_json() if args.format == "json" else creation_blueprint_markdown(), args.output)
        return 0
    if args.creation_command == "plan":
        plan = create_plan(args.project_type, args.goal)
        _write_output(creation_plan_json(plan) if args.format == "json" else creation_plan_markdown(plan), args.output)
        return 0
    raise ValueError(f"unknown creation command: {args.creation_command}")


def _handle_environment(args: argparse.Namespace) -> int:
    if args.environment_command == "inspect":
        report = inspect_environment(profile=args.profile)
        _write_output(environment_json(report) if args.format == "json" else environment_markdown(report), args.output)
        return 0
    raise ValueError(f"unknown environment command: {args.environment_command}")


def _handle_mastery(args: argparse.Namespace) -> int:
    if args.mastery_command == "profile":
        profile = level_10_mastery_profile(args.applies_to)
        _write_output(mastery_json(profile) if args.format == "json" else mastery_markdown(profile), args.output)
        return 0
    raise ValueError(f"unknown mastery command: {args.mastery_command}")


def _handle_maintainability(args: argparse.Namespace) -> int:
    if args.maintainability_command == "audit":
        report = audit_maintainability(Path(args.path), warn_lines=args.warn_lines, hold_lines=args.hold_lines)
        _write_output(maintainability_json(report) if args.format == "json" else maintainability_markdown(report), args.output)
        return 0 if report.verdict == "PASS" else 17
    raise ValueError(f"unknown maintainability command: {args.maintainability_command}")


def _handle_file(args: argparse.Namespace) -> int:
    if args.file_command == "inventory":
        inventory = build_inventory(Path(args.path), max_files=args.max_files)
        _write_output(inventory_json(inventory) if args.format == "json" else inventory_markdown(inventory), args.output)
        return 0
    if args.file_command == "organize-plan":
        plan = plan_organize(Path(args.path), strategy=args.strategy, max_files=args.max_files)
        _write_output(organize_plan_json(plan) if args.format == "json" else organize_plan_markdown(plan), args.output)
        return 0
    raise ValueError(f"unknown file command: {args.file_command}")


def _handle_file_runtime(args: argparse.Namespace) -> int:
    if args.file_runtime_command == "apply":
        result = apply_file_transaction(Path(args.plan), Path(args.request), Path(args.decision), dry_run=not args.apply, manifest=Path(args.manifest) if args.manifest else None)
        _write_output(file_transaction_json(result) if args.format == "json" else file_transaction_markdown(result), args.output)
        return 0
    if args.file_runtime_command == "undo":
        result = undo_file_transaction(Path(args.manifest))
        _write_output(file_transaction_json(result) if args.format == "json" else file_transaction_markdown(result), args.output)
        return 0
    raise ValueError(f"unknown file-runtime command: {args.file_runtime_command}")


def _handle_bug(args: argparse.Namespace) -> int:
    if args.bug_command == "find":
        report = find_bugs(Path(args.path), failure=args.failure, max_files=args.max_files, max_file_bytes=args.max_file_bytes)
        _write_output(bug_report_json(report) if args.format == "json" else bug_report_markdown(report), args.output)
        return 0 if report.verdict == "PASS" else 16
    raise ValueError(f"unknown bug command: {args.bug_command}")


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

    item = subparsers.add_parser("capability", help="Inspect public capability status and policy model")
    capability_subparsers = item.add_subparsers(dest="capability_command", required=True)
    capability_item = capability_subparsers.add_parser("list", help="List capability definitions")
    capability_item.add_argument("--status", choices=("WORKING", "EXPERIMENTAL", "PLAN-ONLY", "UNSUPPORTED"))
    capability_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    capability_item.add_argument("--output", "-o")
    capability_item.set_defaults(handler=_handle_capability)
    capability_item = capability_subparsers.add_parser("show", help="Show one capability definition")
    capability_item.add_argument("capability_id")
    capability_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    capability_item.add_argument("--output", "-o")
    capability_item.set_defaults(handler=_handle_capability)
    capability_item = capability_subparsers.add_parser("validate", help="Validate capability registry invariants")
    capability_item.add_argument("--output", "-o")
    capability_item.set_defaults(handler=_handle_capability)

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

    item = subparsers.add_parser("runtime", help="Create capability-gated runtime kernel requests and audit records")
    runtime_subparsers = item.add_subparsers(dest="runtime_command", required=True)
    runtime_item = runtime_subparsers.add_parser("request", help="Create a hash-bound capability request")
    runtime_item.add_argument("capability")
    runtime_item.add_argument("intent")
    runtime_item.add_argument("--target")
    runtime_item.add_argument("--request-id", default="RUNTIME-0001")
    runtime_item.add_argument("--cwd")
    runtime_item.add_argument("--write", action="store_true")
    runtime_item.add_argument("--network", action="store_true")
    runtime_item.add_argument("--timeout-seconds", type=int, default=60)
    runtime_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    runtime_item.add_argument("--output", "-o")
    runtime_item.add_argument("--cmd", dest="command", nargs=argparse.REMAINDER)
    runtime_item.set_defaults(handler=_handle_runtime)
    runtime_item = runtime_subparsers.add_parser("decide", help="Record a human decision bound to a runtime request hash")
    runtime_item.add_argument("request")
    runtime_item.add_argument("--approved", action="store_true")
    runtime_item.add_argument("--approver", required=True)
    runtime_item.add_argument("--reason", required=True)
    runtime_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    runtime_item.add_argument("--output", "-o")
    runtime_item.set_defaults(handler=_handle_runtime)
    runtime_item = runtime_subparsers.add_parser("audit", help="Create a runtime audit event without executing OS actions")
    runtime_item.add_argument("request")
    runtime_item.add_argument("--decision")
    runtime_item.add_argument("--outcome", default="planned")
    runtime_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    runtime_item.add_argument("--output", "-o")
    runtime_item.set_defaults(handler=_handle_runtime)

    item = subparsers.add_parser("audit-log", help="Append and verify tamper-evident runtime audit logs")
    audit_log_subparsers = item.add_subparsers(dest="audit_log_command", required=True)
    audit_log_item = audit_log_subparsers.add_parser("append", help="Append a runtime audit event to a hash-chain log")
    audit_log_item.add_argument("log")
    audit_log_item.add_argument("event")
    audit_log_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    audit_log_item.add_argument("--output", "-o")
    audit_log_item.set_defaults(handler=_handle_audit_log)
    audit_log_item = audit_log_subparsers.add_parser("verify", help="Verify an audit log hash chain")
    audit_log_item.add_argument("log")
    audit_log_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    audit_log_item.add_argument("--output", "-o")
    audit_log_item.set_defaults(handler=_handle_audit_log)

    item = subparsers.add_parser("sandbox", help="Create sandbox policies and safe subprocess plans")
    sandbox_subparsers = item.add_subparsers(dest="sandbox_command", required=True)
    sandbox_item = sandbox_subparsers.add_parser("init", help="Create a default sandbox policy")
    sandbox_item.add_argument("workspace", nargs="?", default=".")
    sandbox_item.add_argument("--output", "-o", default="sandbox-policy.json")
    sandbox_item.set_defaults(handler=_handle_sandbox)
    sandbox_item = sandbox_subparsers.add_parser("plan", help="Plan a sandboxed command without executing it")
    sandbox_item.add_argument("policy")
    sandbox_item.add_argument("--cwd")
    sandbox_item.add_argument("--write", action="store_true")
    sandbox_item.add_argument("--network", action="store_true")
    sandbox_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    sandbox_item.add_argument("--output", "-o")
    sandbox_item.add_argument("--cmd", dest="command", nargs=argparse.REMAINDER, required=True)
    sandbox_item.set_defaults(handler=_handle_sandbox)
    sandbox_item = sandbox_subparsers.add_parser("run", help="Run an allowlisted command with sandbox policy checks")
    sandbox_item.add_argument("policy")
    sandbox_item.add_argument("request")
    sandbox_item.add_argument("decision")
    sandbox_item.add_argument("--cwd")
    sandbox_item.add_argument("--write", action="store_true")
    sandbox_item.add_argument("--network", action="store_true")
    sandbox_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    sandbox_item.add_argument("--output", "-o")
    sandbox_item.add_argument("--cmd", dest="command", nargs=argparse.REMAINDER, required=True)
    sandbox_item.set_defaults(handler=_handle_sandbox)

    item = subparsers.add_parser("workspace", help="Initialize SQLite-backed TStack workspaces")
    workspace_subparsers = item.add_subparsers(dest="workspace_command", required=True)
    workspace_item = workspace_subparsers.add_parser("init", help="Initialize runtime workspace state")
    workspace_item.add_argument("path", nargs="?", default=".")
    workspace_item.add_argument("--output", "-o")
    workspace_item.set_defaults(handler=_handle_workspace)
    workspace_item = workspace_subparsers.add_parser("export", help="Export portable runtime state without approval key material")
    workspace_item.add_argument("--workspace", default=".")
    workspace_item.add_argument("--output", "-o", required=True)
    workspace_item.set_defaults(handler=_handle_workspace)
    workspace_item = workspace_subparsers.add_parser("import", help="Import portable runtime state into a workspace")
    workspace_item.add_argument("bundle")
    workspace_item.add_argument("--workspace", default=".")
    workspace_item.add_argument("--output", "-o")
    workspace_item.set_defaults(handler=_handle_workspace)

    item = subparsers.add_parser("daemon", help="Inspect local runtime daemon foundation status")
    daemon_subparsers = item.add_subparsers(dest="daemon_command", required=True)
    daemon_item = daemon_subparsers.add_parser("start", help="Initialize local runtime state and report daemon foundation status")
    daemon_item.add_argument("--workspace", default=".")
    daemon_item.add_argument("--output", "-o")
    daemon_item.set_defaults(handler=_handle_daemon)
    daemon_item = daemon_subparsers.add_parser("recover", help="Recover stale RUNNING tasks after restart")
    daemon_item.add_argument("--workspace", default=".")
    daemon_item.add_argument("--policy", choices=("fail", "requeue"), default="fail")
    daemon_item.add_argument("--output", "-o")
    daemon_item.set_defaults(handler=_handle_daemon)
    daemon_item = daemon_subparsers.add_parser("status", help="Report local runtime state, queue, and audit health")
    daemon_item.add_argument("--workspace", default=".")
    daemon_item.add_argument("--output", "-o")
    daemon_item.set_defaults(handler=_handle_daemon)
    daemon_item = daemon_subparsers.add_parser("run", help="Run the foreground runtime daemon loop")
    daemon_item.add_argument("--workspace", default=".")
    daemon_item.add_argument("--daemon-id")
    daemon_item.add_argument("--cycles", type=int)
    daemon_item.add_argument("--interval-seconds", type=float, default=1.0)
    daemon_item.add_argument("--worker-limit", type=int, default=1)
    daemon_item.add_argument("--recovery-policy", choices=("fail", "requeue"), default="fail")
    daemon_item.add_argument("--output", "-o")
    daemon_item.set_defaults(handler=_handle_daemon)

    item = subparsers.add_parser("task", help="Submit and run runtime kernel tasks")
    task_subparsers = item.add_subparsers(dest="task_command", required=True)
    task_item = task_subparsers.add_parser("submit", help="Submit a filesystem.write task")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--capability", default="filesystem.write")
    task_item.add_argument("--target", required=True)
    task_item.add_argument("--content", required=True)
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("list", help="List runtime tasks")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("show", help="Show one runtime task")
    task_item.add_argument("task_id")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("run", help="Run an approved runtime task")
    task_item.add_argument("task_id")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--timeout-seconds", type=int, default=30)
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("queue", help="Queue an approved runtime task")
    task_item.add_argument("task_id")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("run-next", help="Run the next queued runtime task")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--timeout-seconds", type=int, default=30)
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("events", help="List runtime task events")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--task-id")
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("cancel", help="Cancel a runtime task")
    task_item.add_argument("task_id")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--reason", default="cancelled by user")
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)
    task_item = task_subparsers.add_parser("retry", help="Move a failed or blocked task back to approval review")
    task_item.add_argument("task_id")
    task_item.add_argument("--workspace", default=".")
    task_item.add_argument("--reason", default="retry requested")
    task_item.add_argument("--output", "-o")
    task_item.set_defaults(handler=_handle_task)

    item = subparsers.add_parser("kernel-approval", help="Approve runtime kernel tasks with signed approvals")
    approval_subparsers = item.add_subparsers(dest="kernel_approval_command", required=True)
    approval_item = approval_subparsers.add_parser("approve", help="Create a signed task approval")
    approval_item.add_argument("task_id")
    approval_item.add_argument("--workspace", default=".")
    approval_item.add_argument("--actor", required=True)
    approval_item.add_argument("--mode", default="ONCE")
    approval_item.add_argument("--expires-at")
    approval_item.add_argument("--max-uses", type=int, default=1)
    approval_item.add_argument("--output", "-o")
    approval_item.set_defaults(handler=_handle_kernel_approval)
    approval_item = approval_subparsers.add_parser("revoke", help="Revoke a signed task approval")
    approval_item.add_argument("approval_id")
    approval_item.add_argument("--workspace", default=".")
    approval_item.add_argument("--actor", required=True)
    approval_item.add_argument("--reason", required=True)
    approval_item.add_argument("--output", "-o")
    approval_item.set_defaults(handler=_handle_kernel_approval)

    item = subparsers.add_parser("kernel-rollback", help="Rollback runtime kernel tasks")
    rollback_subparsers = item.add_subparsers(dest="kernel_rollback_command", required=True)
    rollback_item = rollback_subparsers.add_parser("apply", help="Apply rollback for a task")
    rollback_item.add_argument("task_id")
    rollback_item.add_argument("--workspace", default=".")
    rollback_item.add_argument("--output", "-o")
    rollback_item.set_defaults(handler=_handle_kernel_rollback)

    item = subparsers.add_parser("kernel-audit", help="Verify runtime kernel audit chain")
    audit_subparsers = item.add_subparsers(dest="kernel_audit_command", required=True)
    audit_item = audit_subparsers.add_parser("verify", help="Verify SQLite audit hash chain")
    audit_item.add_argument("--workspace", default=".")
    audit_item.add_argument("--output", "-o")
    audit_item.set_defaults(handler=_handle_kernel_audit)

    item = subparsers.add_parser("worker", help="Run bounded same-process worker pool over queued tasks")
    worker_subparsers = item.add_subparsers(dest="worker_command", required=True)
    worker_item = worker_subparsers.add_parser("run", help="Process queued tasks with bounded same-process workers")
    worker_item.add_argument("--workspace", default=".")
    worker_item.add_argument("--workers", type=int, default=1)
    worker_item.add_argument("--limit", type=int)
    worker_item.add_argument("--timeout-seconds", type=int, default=30)
    worker_item.add_argument("--output", "-o")
    worker_item.set_defaults(handler=_handle_worker)

    item = subparsers.add_parser("benchmark", help="Run machine-readable kernel benchmarks")
    benchmark_subparsers = item.add_subparsers(dest="benchmark_command", required=True)
    benchmark_item = benchmark_subparsers.add_parser("kernel", help="Benchmark queued task execution in the local kernel")
    benchmark_item.add_argument("--workspace", default=".benchmark-workspace")
    benchmark_item.add_argument("--tasks", type=int, default=100)
    benchmark_item.add_argument("--workers", type=int, default=4)
    benchmark_item.add_argument("--output", "-o")
    benchmark_item.set_defaults(handler=_handle_benchmark)

    item = subparsers.add_parser("desktop", help="Inspect local-first desktop Agentic OS blueprint")
    desktop_subparsers = item.add_subparsers(dest="desktop_command", required=True)
    desktop_item = desktop_subparsers.add_parser("blueprint", help="Show local-first desktop system architecture")
    desktop_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    desktop_item.add_argument("--output", "-o")
    desktop_item.set_defaults(handler=_handle_desktop)
    item = subparsers.add_parser("creation", help="Inspect local-first Creation OS blueprint")
    creation_subparsers = item.add_subparsers(dest="creation_command", required=True)
    creation_item = creation_subparsers.add_parser("blueprint", help="Show 3D, game, web, and mobile creation architecture")
    creation_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    creation_item.add_argument("--output", "-o")
    creation_item.set_defaults(handler=_handle_creation)
    creation_item = creation_subparsers.add_parser("plan", help="Create a project-specific Creation OS plan")
    creation_item.add_argument("project_type")
    creation_item.add_argument("goal")
    creation_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    creation_item.add_argument("--output", "-o")
    creation_item.set_defaults(handler=_handle_creation)
    item = subparsers.add_parser("environment", help="Inspect local tools for Creation OS profiles")
    environment_subparsers = item.add_subparsers(dest="environment_command", required=True)
    environment_item = environment_subparsers.add_parser("inspect", help="Detect local tools and missing dependencies")
    environment_item.add_argument("--profile", choices=("all", "core", "web", "devops", "3d", "game", "mobile", "media"), default="all")
    environment_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    environment_item.add_argument("--output", "-o")
    environment_item.set_defaults(handler=_handle_environment)
    item = subparsers.add_parser("mastery", help="Inspect Level 10 mastery standards for agents")
    mastery_subparsers = item.add_subparsers(dest="mastery_command", required=True)
    mastery_item = mastery_subparsers.add_parser("profile", help="Show master architect/programmer operating standard")
    mastery_item.add_argument("--applies-to", default="all-agents")
    mastery_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    mastery_item.add_argument("--output", "-o")
    mastery_item.set_defaults(handler=_handle_mastery)

    item = subparsers.add_parser("maintainability", help="Audit module size and maintainability risks")
    maintainability_subparsers = item.add_subparsers(dest="maintainability_command", required=True)
    maintainability_item = maintainability_subparsers.add_parser("audit", help="Report oversized modules and test/source balance")
    maintainability_item.add_argument("path", nargs="?", default=".")
    maintainability_item.add_argument("--warn-lines", type=int, default=500)
    maintainability_item.add_argument("--hold-lines", type=int, default=1200)
    maintainability_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    maintainability_item.add_argument("--output", "-o")
    maintainability_item.set_defaults(handler=_handle_maintainability)

    item = subparsers.add_parser("file", help="Run local-first file agent inventory and duplicate analysis")
    file_subparsers = item.add_subparsers(dest="file_command", required=True)
    file_item = file_subparsers.add_parser("inventory", help="Scan local files and detect duplicate content")
    file_item.add_argument("path", nargs="?", default=".")
    file_item.add_argument("--max-files", type=int, default=5000)
    file_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    file_item.add_argument("--output", "-o")
    file_item.set_defaults(handler=_handle_file)
    file_item = file_subparsers.add_parser("organize-plan", help="Plan safe file organization without moving files")
    file_item.add_argument("path", nargs="?", default=".")
    file_item.add_argument("--strategy", choices=("extension", "year"), default="extension")
    file_item.add_argument("--max-files", type=int, default=5000)
    file_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    file_item.add_argument("--output", "-o")
    file_item.set_defaults(handler=_handle_file)

    item = subparsers.add_parser("file-runtime", help="Apply and undo approved file organization transactions")
    file_runtime_subparsers = item.add_subparsers(dest="file_runtime_command", required=True)
    file_runtime_item = file_runtime_subparsers.add_parser("apply", help="Dry-run or apply an approved file move plan")
    file_runtime_item.add_argument("plan")
    file_runtime_item.add_argument("request")
    file_runtime_item.add_argument("decision")
    file_runtime_item.add_argument("--apply", action="store_true")
    file_runtime_item.add_argument("--manifest")
    file_runtime_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    file_runtime_item.add_argument("--output", "-o")
    file_runtime_item.set_defaults(handler=_handle_file_runtime)
    file_runtime_item = file_runtime_subparsers.add_parser("undo", help="Undo an applied file transaction from its manifest")
    file_runtime_item.add_argument("manifest")
    file_runtime_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    file_runtime_item.add_argument("--output", "-o")
    file_runtime_item.set_defaults(handler=_handle_file_runtime)

    item = subparsers.add_parser("bug", help="Find bugs and route fix plans to responsible agents")
    bug_subparsers = item.add_subparsers(dest="bug_command", required=True)
    bug_item = bug_subparsers.add_parser("find", help="Create a bug report from scan findings and optional failure text")
    bug_item.add_argument("path", nargs="?", default=".")
    bug_item.add_argument("--failure")
    bug_item.add_argument("--max-files", type=int, default=10000)
    bug_item.add_argument("--max-file-bytes", type=int, default=1000000)
    bug_item.add_argument("--format", choices=("markdown", "json"), default="markdown")
    bug_item.add_argument("--output", "-o")
    bug_item.set_defaults(handler=_handle_bug)
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

"""Approval-gated agentic delivery planning for TStack."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


AGENT_PLAN_SCHEMA = "tstack-agent-plan/v1"


@dataclass(frozen=True)
class AgentPhase:
    id: str
    name: str
    objective: str
    agents: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    quality_gates: tuple[str, ...]
    approval_required: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True)
class AgentPlan:
    schema: str
    goal: str
    mode: str
    verdict: str
    phases: tuple[AgentPhase, ...]
    guardrails: tuple[str, ...]


def build_agent_plan(goal: str, *, mode: str = "plan-only", include_uiux: bool = True, include_deployment: bool = True) -> AgentPlan:
    cleaned_goal = goal.strip()
    if not cleaned_goal:
        raise ValueError("agent goal is required")
    if mode != "plan-only":
        raise ValueError("only plan-only agent mode is currently supported")

    phases: list[AgentPhase] = [
        AgentPhase(
            id="AGENT-001",
            name="Discovery and Research",
            objective="Collect requirements, constraints, source material, competitor signals, and available project evidence.",
            agents=("research-agent", "product-agent", "knowledge-agent"),
            inputs=("user goal", "repository context", "approved public sources", "existing documentation"),
            outputs=("requirements brief", "evidence log", "open questions", "risk assumptions"),
            quality_gates=("source attribution", "no private scraping without approval", "requirements reviewed"),
        ),
        AgentPhase(
            id="AGENT-002",
            name="Architecture Planning",
            objective="Convert requirements into system architecture, data model, APIs, module boundaries, and delivery plan.",
            agents=("architect-agent", "security-agent", "performance-agent"),
            inputs=("requirements brief", "knowledge packs", "existing architecture", "constraints"),
            outputs=("architecture plan", "API plan", "data plan", "risk register", "rollback strategy"),
            quality_gates=("architecture evidence", "security threat model", "operational constraints documented"),
        ),
    ]

    if include_uiux:
        phases.append(
            AgentPhase(
                id="AGENT-003",
                name="Advanced UI/UX Design",
                objective="Design high-quality user flows, layouts, interaction states, accessibility, and visual direction.",
                agents=("ui-ux-agent", "design-system-agent", "accessibility-agent"),
                inputs=("requirements brief", "brand constraints", "target users", "device targets"),
                outputs=("user flows", "wireframes", "design tokens", "component plan", "accessibility checklist"),
                quality_gates=("responsive design review", "accessibility review", "no placeholder-only UI", "design approval"),
            )
        )

    phases.extend(
        [
            AgentPhase(
                id="AGENT-004",
                name="Implementation Plan",
                objective="Break architecture into build tasks with test, documentation, and migration requirements.",
                agents=("developer-agent", "qa-agent", "documentation-agent"),
                inputs=("architecture plan", "UI/UX plan", "repository context", "coding standards"),
                outputs=("task breakdown", "file change plan", "test plan", "documentation plan"),
                quality_gates=("no unapproved destructive changes", "test coverage plan", "backward compatibility review"),
            ),
            AgentPhase(
                id="AGENT-005",
                name="Quality, Security, and Performance",
                objective="Define verification work before release: tests, scans, policy checks, and performance evidence.",
                agents=("qa-agent", "security-agent", "performance-agent"),
                inputs=("implementation plan", "threat model", "release target", "policy files"),
                outputs=("verification checklist", "security review", "performance plan", "release blockers"),
                quality_gates=("CI green", "critical findings resolved", "performance budget reviewed"),
            ),
            AgentPhase(
                id="AGENT-006",
                name="Release Readiness",
                objective="Prepare release evidence, changelog, SBOM, artifact verification, and rollback readiness.",
                agents=("release-agent", "supply-chain-agent", "documentation-agent"),
                inputs=("verified build", "test results", "security results", "release notes"),
                outputs=("release decision", "SBOM", "manifest", "checksums", "evidence bundle"),
                quality_gates=("trust gate pass", "evidence bundle verified", "rollback documented"),
            ),
        ]
    )

    if include_deployment:
        phases.append(
            AgentPhase(
                id="AGENT-007",
                name="Deployment Plan",
                objective="Plan deployment steps, environment checks, monitoring, rollback, and post-release validation.",
                agents=("deployment-agent", "release-agent", "operations-agent"),
                inputs=("release decision", "environment policy", "deployment target", "rollback strategy"),
                outputs=("deployment runbook", "monitoring checklist", "rollback plan", "post-release validation"),
                quality_gates=("human approval", "environment access review", "rollback readiness", "post-deploy smoke tests"),
            )
        )

    return AgentPlan(
        schema=AGENT_PLAN_SCHEMA,
        goal=cleaned_goal,
        mode=mode,
        verdict="REVIEW",
        phases=tuple(phases),
        guardrails=(
            "Agentic mode is plan-only until explicit human approval is implemented.",
            "No scraping of private or authenticated sources without explicit authorization.",
            "No code changes, dependency changes, SSH, deployment, or production actions are executed by this planner.",
            "Every phase requires evidence, quality gates, and rollback or recovery thinking.",
            "UI/UX work must produce usable flows and states, not only visual decoration.",
        ),
    )


def agent_plan_json(plan: AgentPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def agent_plan_markdown(plan: AgentPlan) -> str:
    lines = [
        "# TStack Agentic Delivery Plan",
        "",
        f"- Goal: {plan.goal}",
        f"- Mode: `{plan.mode}`",
        f"- Verdict: **{plan.verdict}**",
        f"- Phases: {len(plan.phases)}",
        "",
        "## Phases",
        "",
    ]
    for phase in plan.phases:
        lines.extend(
            [
                f"### {phase.id} - {phase.name}",
                "",
                f"Objective: {phase.objective}",
                "",
                f"- Agents: {', '.join(phase.agents)}",
                f"- Inputs: {', '.join(phase.inputs)}",
                f"- Outputs: {', '.join(phase.outputs)}",
                f"- Quality gates: {', '.join(phase.quality_gates)}",
                f"- Approval required: {'yes' if phase.approval_required else 'no'}",
                f"- Execution allowed: {'yes' if phase.execution_allowed else 'no'}",
                "",
            ]
        )
    lines.extend(["## Guardrails", ""])
    lines.extend(f"- {item}" for item in plan.guardrails)
    return "\n".join(lines) + "\n"

"""Approval-gated agentic delivery planning for TStack."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


AGENT_PLAN_SCHEMA = "tstack-agent-plan/v1"
AGENT_CATALOG_SCHEMA = "tstack-agent-catalog/v1"


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    name: str
    category: str
    responsibilities: tuple[str, ...]
    permissions: tuple[str, ...]
    approval_required: bool = True
    execution_allowed: bool = False


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


@dataclass(frozen=True)
class AgentSelection:
    schema: str
    goal: str
    selected_agents: tuple[AgentDefinition, ...]
    rationale: tuple[str, ...]
    approval_required: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True)
class OrchestratedPhase:
    phase_id: str
    phase_name: str
    objective: str
    agents: tuple[str, ...]
    outputs: tuple[str, ...]
    approval_required: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True)
class OrchestrationPlan:
    schema: str
    goal: str
    selected_agent_count: int
    phases: tuple[OrchestratedPhase, ...]
    guardrails: tuple[str, ...]
    approval_required: bool = True
    execution_allowed: bool = False


@dataclass(frozen=True)
class AgentStats:
    schema: str
    total_agents: int
    categories: dict[str, int]
    approval_required: int
    execution_allowed: int


@dataclass(frozen=True)
class FailureRoute:
    schema: str
    failure_type: str
    description: str
    primary_agent: str
    supporting_agents: tuple[str, ...]
    escalation_agent: str
    recommended_command: str
    approval_required: bool = True
    execution_allowed: bool = False
    rationale: tuple[str, ...] = ()


AGENT_CATALOG: tuple[AgentDefinition, ...] = (
    AgentDefinition("architect-agent", "Architect Agent", "engineering", ("system architecture", "API boundaries", "data modeling", "technical tradeoffs"), ("read-repo", "write-plan")),
    AgentDefinition("developer-agent", "Developer Agent", "engineering", ("implementation planning", "code generation proposals", "refactoring plans", "bug fix plans"), ("read-repo", "write-plan")),
    AgentDefinition("qa-agent", "QA Agent", "engineering", ("test planning", "regression analysis", "smoke testing", "bug triage"), ("read-repo", "run-local-tests-plan")),
    AgentDefinition("security-agent", "Security Agent", "engineering", ("secret scanning", "threat modeling", "dependency risk", "secure coding review"), ("read-repo", "write-security-report")),
    AgentDefinition("performance-agent", "Performance Agent", "engineering", ("performance budgets", "profiling plans", "capacity risks", "latency review"), ("read-repo", "write-plan")),
    AgentDefinition("documentation-agent", "Documentation Agent", "engineering", ("README updates", "API docs", "release notes", "user guides"), ("read-repo", "write-plan")),
    AgentDefinition("release-agent", "Release Agent", "engineering", ("release planning", "versioning", "changelog", "rollback readiness"), ("read-repo", "write-release-plan")),
    AgentDefinition("supply-chain-agent", "Supply Chain Agent", "engineering", ("SBOM", "checksums", "attestations", "artifact verification"), ("read-artifacts", "write-evidence")),
    AgentDefinition("knowledge-agent", "Knowledge Agent", "engineering", ("knowledge search", "language guidance", "best-practice retrieval", "pack validation"), ("read-knowledge",)),
    AgentDefinition("research-agent", "Research Agent", "business", ("public research planning", "competitor analysis", "source logging", "requirements evidence"), ("read-approved-sources",)),
    AgentDefinition("product-agent", "Product Agent", "business", ("requirements", "feature scope", "user stories", "prioritization"), ("write-plan",)),
    AgentDefinition("business-analyst-agent", "Business Analyst Agent", "business", ("process mapping", "business rules", "stakeholder workflows", "ROI framing"), ("write-plan",)),
    AgentDefinition("crm-agent", "CRM Agent", "business", ("leads", "customers", "pipelines", "support workflows"), ("write-plan",)),
    AgentDefinition("erp-agent", "ERP Agent", "business", ("inventory", "procurement", "billing", "operations workflows"), ("write-plan",)),
    AgentDefinition("finance-agent", "Finance Agent", "business", ("billing", "financial reports", "forecasting", "payment workflows"), ("write-plan",)),
    AgentDefinition("hr-agent", "HR Agent", "business", ("attendance", "payroll", "employee records", "HR workflows"), ("write-plan",)),
    AgentDefinition("support-agent", "Customer Support Agent", "business", ("ticketing", "FAQ", "support automation", "escalation paths"), ("write-plan",)),
    AgentDefinition("marketing-agent", "Marketing Agent", "business", ("landing pages", "SEO", "campaigns", "content planning"), ("write-plan",)),
    AgentDefinition("analytics-agent", "Analytics Agent", "data-ai", ("dashboards", "KPI reports", "data quality", "business metrics"), ("read-approved-data", "write-report")),
    AgentDefinition("data-engineering-agent", "Data Engineering Agent", "data-ai", ("ETL plans", "data cleaning", "pipeline design", "schema mapping"), ("write-plan",)),
    AgentDefinition("ai-chatbot-agent", "AI Chatbot Agent", "data-ai", ("chatbot flows", "RAG planning", "tool routing", "safety rules"), ("write-plan",)),
    AgentDefinition("voice-agent", "Voice Assistant Agent", "data-ai", ("speech workflows", "voice commands", "transcription plans", "voice UX"), ("write-plan",)),
    AgentDefinition("vision-agent", "Vision Agent", "data-ai", ("OCR", "image analysis", "visual QA", "document extraction"), ("write-plan",)),
    AgentDefinition("translation-agent", "Translation Agent", "data-ai", ("translation workflows", "localization", "language QA", "tone adaptation"), ("write-plan",)),
    AgentDefinition("recommendation-agent", "Recommendation Agent", "data-ai", ("recommendation logic", "ranking plans", "feedback loops", "evaluation"), ("write-plan",)),
    AgentDefinition("semantic-search-agent", "Semantic Search Agent", "data-ai", ("indexing", "retrieval", "embedding strategy", "search evaluation"), ("write-plan",)),
    AgentDefinition("ui-ux-agent", "UI/UX Agent", "design", ("user flows", "wireframes", "interaction states", "responsive UX"), ("write-design-plan",)),
    AgentDefinition("design-system-agent", "Design System Agent", "design", ("tokens", "components", "visual consistency", "theming"), ("write-design-plan",)),
    AgentDefinition("accessibility-agent", "Accessibility Agent", "design", ("WCAG checks", "keyboard flows", "contrast", "screen reader review"), ("write-a11y-report",)),
    AgentDefinition("frontend-agent", "Frontend Agent", "design", ("frontend architecture", "component planning", "state management", "responsive UI"), ("write-plan",)),
    AgentDefinition("backend-agent", "Backend Agent", "engineering", ("API design", "service boundaries", "database access", "background jobs"), ("write-plan",)),
    AgentDefinition("database-agent", "Database Agent", "engineering", ("schema design", "migrations", "indexes", "data integrity"), ("write-plan",)),
    AgentDefinition("auth-agent", "Authentication Agent", "engineering", ("login flows", "sessions", "RBAC", "identity provider integration"), ("write-plan",)),
    AgentDefinition("admin-panel-agent", "Admin Panel Agent", "engineering", ("admin workflows", "moderation tools", "operations screens", "permissions"), ("write-plan",)),
    AgentDefinition("mobile-agent", "Mobile Agent", "engineering", ("mobile UX", "offline behavior", "app architecture", "release stores"), ("write-plan",)),
    AgentDefinition("seo-agent", "SEO Agent", "business", ("metadata", "structured data", "content strategy", "crawlability"), ("write-plan",)),
    AgentDefinition("devops-agent", "DevOps Agent", "operations", ("Docker", "CI/CD", "deployment scripts", "environment strategy"), ("write-plan",)),
    AgentDefinition("monitoring-agent", "Monitoring Agent", "operations", ("logs", "metrics", "alerts", "SLOs"), ("write-plan",)),
    AgentDefinition("backup-agent", "Backup Agent", "operations", ("backup plans", "restore tests", "retention", "disaster recovery"), ("write-plan",)),
    AgentDefinition("rollback-agent", "Rollback Agent", "operations", ("rollback plans", "release safety", "recovery drills", "failure playbooks"), ("write-plan",)),
    AgentDefinition("deployment-agent", "Deployment Agent", "operations", ("deployment runbooks", "environment checks", "post-release validation", "release sequencing"), ("write-plan",)),
    AgentDefinition("operations-agent", "Operations Agent", "operations", ("incident response", "runbooks", "maintenance", "operational readiness"), ("write-plan",)),
    AgentDefinition("governance-agent", "Governance Agent", "governance", ("approval workflows", "policy management", "audit controls", "risk register"), ("write-plan",)),
    AgentDefinition("rbac-agent", "RBAC Agent", "governance", ("roles", "permissions", "access reviews", "least privilege"), ("write-plan",)),
    AgentDefinition("audit-agent", "Audit Agent", "governance", ("audit logs", "evidence trails", "compliance reporting", "change history"), ("write-report",)),
    AgentDefinition("compliance-agent", "Compliance Agent", "governance", ("compliance mapping", "control evidence", "policy checks", "exception tracking"), ("write-report",)),
    AgentDefinition("policy-agent", "Policy Agent", "governance", ("policy as code", "exceptions", "gates", "allowlists"), ("write-plan",)),
    AgentDefinition("orchestrator-agent", "Orchestrator Agent", "orchestration", ("agent routing", "conflict resolution", "final decision", "human handoff"), ("coordinate-agents",)),
    AgentDefinition("website-builder-agent", "Website Builder Agent", "orchestration", ("site requirements", "sitemap", "frontend/backend plan", "deployment plan"), ("coordinate-agents",)),
    AgentDefinition("scraping-agent", "Scraping Agent", "orchestration", ("approved public scraping plans", "source rules", "robots review", "data extraction plan"), ("write-plan",)),
    AgentDefinition("integration-agent", "Integration Agent", "orchestration", ("third-party APIs", "webhooks", "sync jobs", "error handling"), ("write-plan",)),
)


def list_agents(category: str | None = None) -> tuple[AgentDefinition, ...]:
    agents = AGENT_CATALOG
    if category:
        agents = tuple(agent for agent in agents if agent.category == category)
    return tuple(sorted(agents, key=lambda item: (item.category, item.id)))


def get_agent(agent_id: str) -> AgentDefinition:
    for agent in AGENT_CATALOG:
        if agent.id == agent_id:
            return agent
    raise KeyError(f"unknown agent: {agent_id}")


def select_agents_for_goal(goal: str) -> AgentSelection:
    cleaned_goal = goal.strip()
    if not cleaned_goal:
        raise ValueError("agent goal is required")
    lowered = cleaned_goal.lower()
    selected: set[str] = {"orchestrator-agent", "product-agent", "architect-agent", "security-agent", "qa-agent", "documentation-agent"}
    rationale = ["Base delivery requires product, architecture, security, QA, documentation, and orchestration agents."]

    def include(ids: tuple[str, ...], reason: str) -> None:
        selected.update(ids)
        rationale.append(reason)

    if any(term in lowered for term in ("website", "landing", "web app", "frontend", "ui", "ux", "dashboard", "admin panel")):
        include(("website-builder-agent", "ui-ux-agent", "design-system-agent", "accessibility-agent", "frontend-agent", "seo-agent"), "Website or UI wording requires design, frontend, accessibility, and SEO agents.")
    if any(term in lowered for term in ("api", "backend", "database", "auth", "login", "crm", "erp", "management system")):
        include(("backend-agent", "database-agent", "auth-agent", "admin-panel-agent"), "Application backend wording requires API, database, authentication, and admin workflow agents.")
    if any(term in lowered for term in ("ai", "chatbot", "rag", "voice", "ocr", "image", "semantic", "recommendation", "translation")):
        include(("ai-chatbot-agent", "semantic-search-agent", "voice-agent", "vision-agent", "recommendation-agent", "translation-agent"), "AI feature wording requires AI, retrieval, voice, vision, recommendation, or translation specialists.")
    if any(term in lowered for term in ("data", "analytics", "dashboard", "kpi", "forecast", "report", "etl")):
        include(("analytics-agent", "data-engineering-agent"), "Data or analytics wording requires analytics and data engineering agents.")
    if any(term in lowered for term in ("deploy", "deployment", "docker", "ci", "cd", "monitor", "backup", "rollback", "devops")):
        include(("devops-agent", "deployment-agent", "monitoring-agent", "backup-agent", "rollback-agent", "operations-agent", "release-agent", "supply-chain-agent"), "Deployment or operations wording requires DevOps, release, monitoring, backup, and rollback agents.")
    if any(term in lowered for term in ("business", "billing", "invoice", "inventory", "payroll", "attendance", "hr", "support", "marketing")):
        include(("business-analyst-agent", "crm-agent", "erp-agent", "finance-agent", "hr-agent", "support-agent", "marketing-agent"), "Business workflow wording requires business, CRM, ERP, finance, HR, support, or marketing agents.")
    if any(term in lowered for term in ("governance", "rbac", "audit", "compliance", "policy", "approval")):
        include(("governance-agent", "rbac-agent", "audit-agent", "compliance-agent", "policy-agent"), "Governance wording requires RBAC, audit, compliance, policy, and approval agents.")

    agents = tuple(get_agent(agent_id) for agent_id in sorted(selected))
    return AgentSelection(
        schema="tstack-agent-selection/v1",
        goal=cleaned_goal,
        selected_agents=agents,
        rationale=tuple(rationale),
    )


def agent_selection_json(selection: AgentSelection) -> str:
    return json.dumps(asdict(selection), indent=2, sort_keys=True) + "\n"


def agent_selection_markdown(selection: AgentSelection) -> str:
    lines = [
        "# TStack Agent Selection",
        "",
        f"- Goal: {selection.goal}",
        f"- Agents selected: {len(selection.selected_agents)}",
        f"- Approval required: {'yes' if selection.approval_required else 'no'}",
        f"- Execution allowed: {'yes' if selection.execution_allowed else 'no'}",
        "",
        "## Selected Agents",
        "",
    ]
    lines.extend(f"- `{agent.id}` - {agent.name} ({agent.category})" for agent in selection.selected_agents)
    lines.extend(["", "## Rationale", ""])
    lines.extend(f"- {reason}" for reason in selection.rationale)
    return "\n".join(lines) + "\n"


def build_orchestration_plan(goal: str) -> OrchestrationPlan:
    selection = select_agents_for_goal(goal)
    selected = {agent.id for agent in selection.selected_agents}

    def present(agent_ids: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(agent_id for agent_id in agent_ids if agent_id in selected)

    phases = (
        OrchestratedPhase(
            "ORCH-001",
            "Discovery and Requirements",
            "Clarify goal, collect evidence, define users, scope, constraints, and open questions.",
            present(("orchestrator-agent", "product-agent", "research-agent", "business-analyst-agent", "knowledge-agent")),
            ("requirements brief", "evidence log", "open questions", "initial risks"),
        ),
        OrchestratedPhase(
            "ORCH-002",
            "Architecture and Data",
            "Design system architecture, APIs, data model, authentication, and module boundaries.",
            present(("architect-agent", "backend-agent", "database-agent", "auth-agent", "security-agent", "performance-agent")),
            ("architecture plan", "API plan", "database plan", "threat model"),
        ),
        OrchestratedPhase(
            "ORCH-003",
            "Advanced UI/UX",
            "Create user flows, responsive layouts, accessibility requirements, and design-system direction.",
            present(("ui-ux-agent", "design-system-agent", "accessibility-agent", "frontend-agent", "seo-agent")),
            ("user flows", "wireframe plan", "component plan", "accessibility checklist"),
        ),
        OrchestratedPhase(
            "ORCH-004",
            "Business and AI Features",
            "Plan domain workflows, analytics, AI features, support flows, and integrations.",
            present(("crm-agent", "erp-agent", "finance-agent", "hr-agent", "support-agent", "marketing-agent", "analytics-agent", "data-engineering-agent", "ai-chatbot-agent", "semantic-search-agent", "voice-agent", "vision-agent", "translation-agent", "recommendation-agent", "integration-agent")),
            ("feature workflow plan", "AI/data plan", "integration plan", "business rules"),
        ),
        OrchestratedPhase(
            "ORCH-005",
            "Implementation and Verification",
            "Plan implementation tasks, tests, documentation, security checks, and performance evidence.",
            present(("developer-agent", "frontend-agent", "backend-agent", "qa-agent", "security-agent", "performance-agent", "documentation-agent")),
            ("task plan", "test plan", "security checklist", "documentation plan"),
        ),
        OrchestratedPhase(
            "ORCH-006",
            "Release and Deployment",
            "Plan build, release evidence, deployment, monitoring, backup, rollback, and post-release validation.",
            present(("release-agent", "supply-chain-agent", "devops-agent", "deployment-agent", "monitoring-agent", "backup-agent", "rollback-agent", "operations-agent")),
            ("release plan", "deployment runbook", "monitoring plan", "rollback plan"),
        ),
        OrchestratedPhase(
            "ORCH-007",
            "Governance and Approval",
            "Review policy, RBAC, audit, compliance, approvals, and final human decision.",
            present(("governance-agent", "rbac-agent", "audit-agent", "compliance-agent", "policy-agent", "orchestrator-agent")),
            ("approval packet", "policy review", "audit plan", "final decision"),
        ),
    )
    return OrchestrationPlan(
        schema="tstack-agent-orchestration/v1",
        goal=selection.goal,
        selected_agent_count=len(selection.selected_agents),
        phases=phases,
        guardrails=(
            "The orchestration plan coordinates agents but does not execute actions.",
            "Every phase remains human-approval gated.",
            "Private scraping, SSH, code changes, and deployment require explicit future approval controls.",
            "Each phase must produce evidence and verification outputs.",
        ),
    )


def orchestration_json(plan: OrchestrationPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def orchestration_markdown(plan: OrchestrationPlan) -> str:
    lines = [
        "# TStack Agent Orchestration Plan",
        "",
        f"- Goal: {plan.goal}",
        f"- Selected agents: {plan.selected_agent_count}",
        f"- Phases: {len(plan.phases)}",
        f"- Approval required: {'yes' if plan.approval_required else 'no'}",
        f"- Execution allowed: {'yes' if plan.execution_allowed else 'no'}",
        "",
    ]
    for phase in plan.phases:
        lines.extend(
            [
                f"## {phase.phase_id} - {phase.phase_name}",
                "",
                phase.objective,
                "",
                f"- Agents: {', '.join(phase.agents) if phase.agents else 'not selected for this goal'}",
                f"- Outputs: {', '.join(phase.outputs)}",
                f"- Approval required: {'yes' if phase.approval_required else 'no'}",
                f"- Execution allowed: {'yes' if phase.execution_allowed else 'no'}",
                "",
            ]
        )
    lines.extend(["## Guardrails", ""])
    lines.extend(f"- {item}" for item in plan.guardrails)
    return "\n".join(lines) + "\n"


def agent_catalog_json(agents: tuple[AgentDefinition, ...]) -> str:
    return json.dumps({"schema": AGENT_CATALOG_SCHEMA, "count": len(agents), "agents": [asdict(agent) for agent in agents]}, indent=2, sort_keys=True) + "\n"


def agent_catalog_markdown(agents: tuple[AgentDefinition, ...]) -> str:
    lines = ["# TStack Agent Catalog", "", f"- Agents: {len(agents)}", ""]
    current = None
    for agent in agents:
        if agent.category != current:
            current = agent.category
            lines.extend([f"## {current.title()}", ""])
        lines.append(f"- `{agent.id}` - {agent.name}: {', '.join(agent.responsibilities)}")
    return "\n".join(lines) + "\n"


def agent_stats() -> AgentStats:
    categories: dict[str, int] = {}
    for agent in AGENT_CATALOG:
        categories[agent.category] = categories.get(agent.category, 0) + 1
    return AgentStats(
        schema="tstack-agent-stats/v1",
        total_agents=len(AGENT_CATALOG),
        categories=dict(sorted(categories.items())),
        approval_required=sum(1 for agent in AGENT_CATALOG if agent.approval_required),
        execution_allowed=sum(1 for agent in AGENT_CATALOG if agent.execution_allowed),
    )


def agent_stats_json(stats: AgentStats) -> str:
    return json.dumps(asdict(stats), indent=2, sort_keys=True) + "\n"


def agent_stats_markdown(stats: AgentStats) -> str:
    lines = [
        "# TStack Agent Stats",
        "",
        f"- Total agents: {stats.total_agents}",
        f"- Approval required: {stats.approval_required}",
        f"- Execution allowed: {stats.execution_allowed}",
        "",
        "## Categories",
        "",
    ]
    lines.extend(f"- `{category}`: {count}" for category, count in stats.categories.items())
    return "\n".join(lines) + "\n"


def route_failure(description: str, *, failure_type: str = "auto") -> FailureRoute:
    text = description.strip()
    if not text:
        raise ValueError("failure description is required")
    lowered = text.lower()
    detected = failure_type
    if failure_type == "auto":
        if any(term in lowered for term in ("security", "secret", "vulnerability", "cve", "auth", "xss", "sql injection")):
            detected = "security"
        elif any(term in lowered for term in ("performance", "slow", "latency", "timeout", "memory", "cpu")):
            detected = "performance"
        elif any(term in lowered for term in ("deploy", "docker", "kubernetes", "ci", "build", "pipeline", "workflow")):
            detected = "devops"
        elif any(term in lowered for term in ("ui", "ux", "visual", "layout", "accessibility", "responsive")):
            detected = "uiux"
        elif any(term in lowered for term in ("test", "pytest", "assert", "unit", "integration", "regression")):
            detected = "test"
        else:
            detected = "general"

    routes = {
        "test": ("qa-agent", ("developer-agent", "documentation-agent"), "orchestrator-agent", "tstack agent orchestrate \"Fix failing tests\""),
        "security": ("security-agent", ("developer-agent", "qa-agent", "policy-agent"), "orchestrator-agent", "tstack scan ."),
        "performance": ("performance-agent", ("developer-agent", "qa-agent", "monitoring-agent"), "orchestrator-agent", "tstack agent orchestrate \"Investigate performance failure\""),
        "devops": ("devops-agent", ("deployment-agent", "release-agent", "operations-agent"), "orchestrator-agent", "tstack agent orchestrate \"Fix CI or deployment failure\""),
        "uiux": ("ui-ux-agent", ("frontend-agent", "accessibility-agent", "qa-agent"), "orchestrator-agent", "tstack agent orchestrate \"Fix UI/UX failure\""),
        "general": ("developer-agent", ("qa-agent", "architect-agent"), "orchestrator-agent", "tstack agent orchestrate \"Investigate software failure\""),
    }
    primary, supporting, escalation, command = routes.get(detected, routes["general"])
    return FailureRoute(
        schema="tstack-failure-route/v1",
        failure_type=detected,
        description=text,
        primary_agent=primary,
        supporting_agents=supporting,
        escalation_agent=escalation,
        recommended_command=command,
        rationale=(
            f"Failure was classified as {detected}.",
            f"Primary owner is {primary}.",
            "Orchestrator remains final routing and human handoff owner.",
        ),
    )


def failure_route_json(route: FailureRoute) -> str:
    return json.dumps(asdict(route), indent=2, sort_keys=True) + "\n"


def failure_route_markdown(route: FailureRoute) -> str:
    lines = [
        "# TStack Failure Route",
        "",
        f"- Failure type: `{route.failure_type}`",
        f"- Primary agent: `{route.primary_agent}`",
        f"- Supporting agents: {', '.join(route.supporting_agents)}",
        f"- Escalation agent: `{route.escalation_agent}`",
        f"- Recommended command: `{route.recommended_command}`",
        f"- Approval required: {'yes' if route.approval_required else 'no'}",
        f"- Execution allowed: {'yes' if route.execution_allowed else 'no'}",
        "",
        "## Rationale",
        "",
    ]
    lines.extend(f"- {item}" for item in route.rationale)
    return "\n".join(lines) + "\n"


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

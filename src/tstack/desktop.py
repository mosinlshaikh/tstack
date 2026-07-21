"""Local-first desktop agentic system blueprint."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


DESKTOP_BLUEPRINT_SCHEMA = "tstack-desktop-blueprint/v1"


@dataclass(frozen=True)
class DesktopCapability:
    id: str
    name: str
    category: str
    local_first: bool
    external_api_required: bool
    approval_required: bool
    execution_allowed: bool
    description: str


CAPABILITIES: tuple[DesktopCapability, ...] = (
    DesktopCapability("file-agent", "File Manager Agent", "desktop", True, False, True, False, "Search, classify, organize, copy, move, archive, and rollback local files."),
    DesktopCapability("desktop-control-agent", "Desktop Control Agent", "desktop", True, False, True, False, "Open approved apps, inspect windows, take screenshots, and monitor local system state."),
    DesktopCapability("browser-agent", "Browser Automation Agent", "browser", True, False, True, False, "Control local Chromium through Playwright in headless or visible mode."),
    DesktopCapability("permission-controller", "Permission Controller", "security", True, False, True, False, "Enforce allowlists, protected folders, sensitive-action approvals, and autonomy levels."),
    DesktopCapability("audit-rollback", "Audit and Rollback", "security", True, False, True, False, "Record append-only action logs, before-change snapshots, backups, and recovery metadata."),
    DesktopCapability("local-llm", "Local LLM Brain", "ai", True, False, True, False, "Use local Ollama, llama.cpp, ONNX, or GGUF-compatible models when available."),
    DesktopCapability("voice-agent", "Voice Agent", "ai", True, False, True, False, "Use local speech recognition, text-to-speech, and optional wake word components."),
    DesktopCapability("code-agent", "Code Agent", "engineering", True, False, True, False, "Analyze and plan local code changes, tests, builds, and documentation."),
    DesktopCapability("website-builder-agent", "Website Builder Agent", "engineering", True, False, True, False, "Plan and build local website projects with UI/UX, frontend, backend, tests, and deployment plans."),
    DesktopCapability("external-api-plugin", "Optional External API Plugin", "integration", False, True, True, False, "Use cloud APIs only after explicit permission, vault loading, and minimum-scope checks."),
)


def desktop_blueprint() -> dict:
    return {
        "schema": DESKTOP_BLUEPRINT_SCHEMA,
        "product": "TStack Local Agentic Desktop OS",
        "default_mode": "local-first-api-free",
        "recommended_stack": {
            "desktop_shell": "Tauri + React",
            "system_core": "Rust",
            "agent_orchestration": "Python",
            "browser": "Local Chromium + Playwright",
            "storage": "SQLite + local full-text search",
            "local_ai": "Ollama / llama.cpp / ONNX / GGUF",
            "voice": "Whisper.cpp or Vosk + Piper + openWakeWord",
            "secrets": "OS keychain or credential manager",
            "audit": "append-only local logs with rollback metadata",
        },
        "autonomy_levels": [
            {"level": 1, "name": "Observe", "execution_allowed": False},
            {"level": 2, "name": "Recommend", "execution_allowed": False},
            {"level": 3, "name": "Approved Automation", "execution_allowed": True},
            {"level": 4, "name": "Supervised Agent", "execution_allowed": True},
        ],
        "blocked": [
            "unrestricted total PC control",
            "unapproved deletes",
            "unapproved admin commands",
            "unapproved payments or purchases",
            "unapproved public publishing",
            "plain-text secret storage",
        ],
        "capabilities": [asdict(item) for item in CAPABILITIES],
    }


def desktop_blueprint_json() -> str:
    return json.dumps(desktop_blueprint(), indent=2, sort_keys=True) + "\n"


def desktop_blueprint_markdown() -> str:
    payload = desktop_blueprint()
    lines = [
        "# TStack Local Agentic Desktop OS",
        "",
        f"- Default mode: `{payload['default_mode']}`",
        f"- Capabilities: {len(payload['capabilities'])}",
        "",
        "## Recommended Stack",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in payload["recommended_stack"].items())
    lines.extend(["", "## Capabilities", ""])
    for item in CAPABILITIES:
        lines.append(f"- `{item.id}` - {item.name}: {item.description}")
    lines.extend(["", "## Blocked Without Explicit Approval", ""])
    lines.extend(f"- {item}" for item in payload["blocked"])
    return "\n".join(lines) + "\n"

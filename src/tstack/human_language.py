"""Human language registry and typo-tolerant intent parsing."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher


HUMAN_LANGUAGE_REGISTRY_SCHEMA = "tstack-human-language-registry/v1"
HUMAN_INTENT_SCHEMA = "tstack-human-intent/v1"


LANGUAGES: tuple[tuple[str, str], ...] = (
    ('english', 'English'), ('hindi', 'Hindi'), ('hinglish', 'Hinglish'), ('urdu', 'Urdu'),
    ('marathi', 'Marathi'), ('gujarati', 'Gujarati'), ('punjabi', 'Punjabi'), ('bengali', 'Bengali'),
    ('tamil', 'Tamil'), ('telugu', 'Telugu'), ('kannada', 'Kannada'), ('malayalam', 'Malayalam'),
    ('odia', 'Odia'), ('assamese', 'Assamese'), ('nepali', 'Nepali'), ('sanskrit', 'Sanskrit'),
    ('sindhi', 'Sindhi'), ('konkani', 'Konkani'), ('maithili', 'Maithili'), ('bhojpuri', 'Bhojpuri'),
    ('arabic', 'Arabic'), ('persian', 'Persian'), ('turkish', 'Turkish'), ('hebrew', 'Hebrew'),
    ('kurdish', 'Kurdish'), ('pashto', 'Pashto'), ('azerbaijani', 'Azerbaijani'), ('armenian', 'Armenian'),
    ('georgian', 'Georgian'), ('kazakh', 'Kazakh'), ('uzbek', 'Uzbek'), ('tajik', 'Tajik'),
    ('kyrgyz', 'Kyrgyz'), ('mongolian', 'Mongolian'), ('spanish', 'Spanish'), ('french', 'French'),
    ('german', 'German'), ('portuguese', 'Portuguese'), ('italian', 'Italian'), ('dutch', 'Dutch'),
    ('russian', 'Russian'), ('ukrainian', 'Ukrainian'), ('polish', 'Polish'), ('czech', 'Czech'),
    ('romanian', 'Romanian'), ('greek', 'Greek'), ('norwegian', 'Norwegian'), ('swedish', 'Swedish'),
    ('danish', 'Danish'), ('finnish', 'Finnish'), ('hungarian', 'Hungarian'), ('serbian', 'Serbian'),
    ('croatian', 'Croatian'), ('bulgarian', 'Bulgarian'), ('slovak', 'Slovak'), ('slovenian', 'Slovenian'),
    ('lithuanian', 'Lithuanian'), ('latvian', 'Latvian'), ('estonian', 'Estonian'), ('albanian', 'Albanian'),
    ('bosnian', 'Bosnian'), ('macedonian', 'Macedonian'), ('belarusian', 'Belarusian'), ('icelandic', 'Icelandic'),
    ('irish', 'Irish'), ('welsh', 'Welsh'), ('scots-gaelic', 'Scots Gaelic'), ('basque', 'Basque'),
    ('catalan', 'Catalan'), ('galician', 'Galician'), ('maltese', 'Maltese'), ('chinese', 'Chinese'),
    ('japanese', 'Japanese'), ('korean', 'Korean'), ('thai', 'Thai'), ('vietnamese', 'Vietnamese'),
    ('indonesian', 'Indonesian'), ('malay', 'Malay'), ('filipino', 'Filipino'), ('burmese', 'Burmese'),
    ('khmer', 'Khmer'), ('lao', 'Lao'), ('sinhala', 'Sinhala'), ('tibetan', 'Tibetan'),
    ('javanese', 'Javanese'), ('sundanese', 'Sundanese'), ('cebuano', 'Cebuano'), ('hmong', 'Hmong'),
    ('swahili', 'Swahili'), ('afrikaans', 'Afrikaans'), ('amharic', 'Amharic'), ('yoruba', 'Yoruba'),
    ('hausa', 'Hausa'), ('zulu', 'Zulu'), ('somali', 'Somali'), ('igbo', 'Igbo'),
    ('xhosa', 'Xhosa'), ('sesotho', 'Sesotho'), ('setswana', 'Setswana'), ('kinyarwanda', 'Kinyarwanda'),
    ('kirundi', 'Kirundi'), ('shona', 'Shona'), ('malagasy', 'Malagasy'), ('tigrinya', 'Tigrinya'),
    ('oromo', 'Oromo'), ('wolof', 'Wolof'), ('bambara', 'Bambara'), ('fula', 'Fula'),
    ('latin', 'Latin'), ('esperanto', 'Esperanto'), ('haitian-creole', 'Haitian Creole'), ('maori', 'Maori'),
    ('samoan', 'Samoan'), ('tongan', 'Tongan'), ('fijian', 'Fijian'), ('hawaiian', 'Hawaiian'),
    ('greenlandic', 'Greenlandic'), ('quechua', 'Quechua'), ('aymara', 'Aymara'), ('guarani', 'Guarani'),
    ('nahuatl', 'Nahuatl'), ('yiddish', 'Yiddish'), ('luxembourgish', 'Luxembourgish'),
)


INTENT_KEYWORDS = {
    "agent_plan": ("agent", "auto", "automatic", "scrap", "scrape", "build", "deploy", "deployment", "ui", "ux", "design", "scratch", "sraap", "skrap"),
    "knowledge_search": ("search", "find", "dhundo", "knowledge", "language", "pata", "pack"),
    "ssh_plan": ("ssh", "server", "remote", "terminal"),
    "scan": ("scan", "audit", "check", "review", "security"),
    "fix_plan": ("fix", "repair", "solve", "sahi", "thik"),
}

WORD_FIXES = {
    "scrap": "scrape",
    "srap": "scrape",
    "sraap": "scrape",
    "skrap": "scrape",
    "scrach": "scratch",
    "scrath": "scratch",
    "handel": "handle",
    "handal": "handle",
    "exicute": "execute",
    "excute": "execute",
    "exicution": "execution",
    "langauge": "language",
    "langugae": "language",
    "desing": "design",
    "deply": "deploy",
    "deploment": "deployment",
    "pluggin": "plugin",
    "repondory": "repository",
    "repoo": "repo",
}


@dataclass(frozen=True)
class HumanIntent:
    schema: str
    text: str
    normalized_text: str
    detected_language: str
    intent: str
    confidence: float
    suggested_command: str
    execution_allowed: bool
    approval_required: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class HumanExecutionPlan:
    schema: str
    intent: HumanIntent
    routed: bool
    route: str
    execution_allowed: bool
    approval_required: bool
    plan: dict | None
    notes: tuple[str, ...]


def list_human_languages() -> tuple[dict[str, str], ...]:
    return tuple({"id": item[0], "name": item[1]} for item in LANGUAGES)


def human_languages_json() -> str:
    return json.dumps({"schema": HUMAN_LANGUAGE_REGISTRY_SCHEMA, "count": len(LANGUAGES), "languages": list(list_human_languages())}, indent=2) + "\n"


def human_languages_markdown() -> str:
    names = ", ".join(name for _, name in LANGUAGES)
    return f"# TStack Human Languages\n\n- Count: {len(LANGUAGES)}\n- Languages: {names}\n"


def _normalize(text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9+#.-]+", text.lower())
    fixed = [WORD_FIXES.get(word, word) for word in words]
    return " ".join(fixed)


def _detect_language(text: str) -> str:
    lowered = text.lower()
    hinglish_markers = ("karo", "hai", "mujhe", "aap", "repo", "daal", "banao", "sabkuch", "galat")
    if any(marker in lowered for marker in hinglish_markers):
        return "hinglish"
    if re.search(r"[\u0900-\u097f]", text):
        return "hindi"
    if re.search(r"[\u0600-\u06ff]", text):
        return "urdu-arabic-script"
    return "english-or-mixed"


def _score_intent(normalized: str, keywords: tuple[str, ...]) -> float:
    words = normalized.split()
    score = 0.0
    for keyword in keywords:
        if keyword in words or keyword in normalized:
            score += 1.0
            continue
        if words and max(SequenceMatcher(None, keyword, word).ratio() for word in words) >= 0.82:
            score += 0.6
    return score


def parse_intent(text: str) -> HumanIntent:
    normalized = _normalize(text)
    if not normalized:
        raise ValueError("human intent text is required")
    scores = {intent: _score_intent(normalized, keywords) for intent, keywords in INTENT_KEYWORDS.items()}
    intent = max(scores, key=scores.get)
    raw_score = scores[intent]
    if raw_score == 0:
        intent = "clarify"
    confidence = min(0.95, round(0.35 + raw_score / 8, 4)) if intent != "clarify" else 0.25
    suggested = {
        "agent_plan": f'tstack agent plan "{text.strip()}"',
        "knowledge_search": f'tstack knowledge search "{normalized}"',
        "ssh_plan": "tstack ssh plan <target> <command> --policy .tstack/ssh-policy.json",
        "scan": "tstack scan .",
        "fix_plan": "tstack fix .",
        "clarify": "Ask a short clarification before planning execution.",
    }[intent]
    return HumanIntent(
        schema=HUMAN_INTENT_SCHEMA,
        text=text,
        normalized_text=normalized,
        detected_language=_detect_language(text),
        intent=intent,
        confidence=confidence,
        suggested_command=suggested,
        execution_allowed=False,
        approval_required=True,
        notes=(
            "Typos are normalized before intent scoring.",
            "Mixed Hinglish/English input is supported.",
            "Parsed intent can suggest a command, but execution remains approval-gated.",
        ),
    )


def intent_json(intent: HumanIntent) -> str:
    return json.dumps(asdict(intent), indent=2, sort_keys=True) + "\n"


def intent_markdown(intent: HumanIntent) -> str:
    return "\n".join(
        [
            "# TStack Human Intent",
            "",
            f"- Detected language: `{intent.detected_language}`",
            f"- Intent: `{intent.intent}`",
            f"- Confidence: {intent.confidence}",
            f"- Normalized text: `{intent.normalized_text}`",
            f"- Suggested command: `{intent.suggested_command}`",
            f"- Approval required: {'yes' if intent.approval_required else 'no'}",
            f"- Execution allowed: {'yes' if intent.execution_allowed else 'no'}",
            "",
            "## Notes",
            "",
            *[f"- {note}" for note in intent.notes],
        ]
    ) + "\n"


def execution_plan_json(plan: HumanExecutionPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def execution_plan_markdown(plan: HumanExecutionPlan) -> str:
    lines = [
        "# TStack Human Execution Plan",
        "",
        f"- Intent: `{plan.intent.intent}`",
        f"- Route: `{plan.route}`",
        f"- Routed: {'yes' if plan.routed else 'no'}",
        f"- Approval required: {'yes' if plan.approval_required else 'no'}",
        f"- Execution allowed: {'yes' if plan.execution_allowed else 'no'}",
        f"- Suggested command: `{plan.intent.suggested_command}`",
        "",
        "## Normalized Request",
        "",
        plan.intent.normalized_text,
        "",
    ]
    if plan.plan and "phases" in plan.plan:
        lines.extend(["## Routed Plan", "", f"- Schema: `{plan.plan.get('schema')}`", f"- Phases: {len(plan.plan.get('phases', []))}", ""])
        for phase in plan.plan.get("phases", []):
            lines.append(f"- `{phase['id']}` {phase['name']}")
        lines.append("")
    lines.extend(["## Notes", ""])
    lines.extend(f"- {note}" for note in plan.notes)
    return "\n".join(lines) + "\n"

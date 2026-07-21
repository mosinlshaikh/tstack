"""Human language registry and typo-tolerant intent parsing."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher


HUMAN_LANGUAGE_REGISTRY_SCHEMA = "tstack-human-language-registry/v1"
HUMAN_INTENT_SCHEMA = "tstack-human-intent/v1"


LANGUAGES: tuple[tuple[str, str], ...] = (
    ("english", "English"), ("hindi", "Hindi"), ("hinglish", "Hinglish"), ("urdu", "Urdu"),
    ("marathi", "Marathi"), ("gujarati", "Gujarati"), ("punjabi", "Punjabi"), ("bengali", "Bengali"),
    ("tamil", "Tamil"), ("telugu", "Telugu"), ("kannada", "Kannada"), ("malayalam", "Malayalam"),
    ("odia", "Odia"), ("assamese", "Assamese"), ("nepali", "Nepali"), ("sanskrit", "Sanskrit"),
    ("arabic", "Arabic"), ("persian", "Persian"), ("turkish", "Turkish"), ("hebrew", "Hebrew"),
    ("spanish", "Spanish"), ("french", "French"), ("german", "German"), ("portuguese", "Portuguese"),
    ("italian", "Italian"), ("dutch", "Dutch"), ("russian", "Russian"), ("ukrainian", "Ukrainian"),
    ("polish", "Polish"), ("czech", "Czech"), ("romanian", "Romanian"), ("greek", "Greek"),
    ("chinese", "Chinese"), ("japanese", "Japanese"), ("korean", "Korean"), ("thai", "Thai"),
    ("vietnamese", "Vietnamese"), ("indonesian", "Indonesian"), ("malay", "Malay"), ("filipino", "Filipino"),
    ("swahili", "Swahili"), ("afrikaans", "Afrikaans"), ("amharic", "Amharic"), ("yoruba", "Yoruba"),
    ("hausa", "Hausa"), ("zulu", "Zulu"), ("somali", "Somali"), ("latin", "Latin"),
    ("esperanto", "Esperanto"), ("norwegian", "Norwegian"), ("swedish", "Swedish"), ("danish", "Danish"),
    ("finnish", "Finnish"), ("hungarian", "Hungarian"), ("serbian", "Serbian"), ("croatian", "Croatian"),
    ("bulgarian", "Bulgarian"), ("slovak", "Slovak"), ("slovenian", "Slovenian"), ("lithuanian", "Lithuanian"),
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

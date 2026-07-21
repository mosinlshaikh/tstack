import json

from tstack.cli import main
from tstack.human_language import list_human_languages, parse_intent


def test_human_language_registry_has_50_plus_languages() -> None:
    languages = list_human_languages()
    assert len(languages) >= 50
    ids = {item["id"] for item in languages}
    assert {"english", "hindi", "hinglish", "urdu", "arabic", "spanish"}.issubset(ids)


def test_parse_hinglish_typo_agent_intent() -> None:
    parsed = parse_intent("scrap se deploment tak sabkuch handel karo aur ui ux desing bhi")
    assert parsed.detected_language == "hinglish"
    assert parsed.intent == "agent_plan"
    assert "scrape" in parsed.normalized_text
    assert "deployment" in parsed.normalized_text
    assert "handle" in parsed.normalized_text
    assert parsed.execution_allowed is False
    assert parsed.approval_required is True


def test_human_languages_cli_json(capsys) -> None:
    assert main(["human", "languages", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-human-language-registry/v1"
    assert payload["count"] >= 50


def test_human_intent_cli_json(capsys) -> None:
    assert main(["human", "intent", "repo scan karke fix plan banao", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-human-intent/v1"
    assert payload["detected_language"] == "hinglish"
    assert payload["execution_allowed"] is False
    assert payload["approval_required"] is True

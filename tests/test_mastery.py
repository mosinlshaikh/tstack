import json

from tstack.cli import main
from tstack.mastery import level_10_mastery_profile


def test_level_10_mastery_profile_has_quality_gates() -> None:
    profile = level_10_mastery_profile()
    assert profile.schema == "tstack-mastery-profile/v1"
    assert profile.level == 10
    assert "security by default" in profile.principles
    assert "tests planned or executed" in profile.quality_gates
    assert "unapproved deployment or publishing" in profile.forbidden_behaviors
    assert profile.execution_allowed is False


def test_mastery_profile_cli_json(capsys) -> None:
    assert main(["mastery", "profile", "--applies-to", "engineering-agents", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-mastery-profile/v1"
    assert payload["level"] == 10
    assert payload["applies_to"] == "engineering-agents"

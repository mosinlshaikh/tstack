"""Regression tests for TStack's extensible rule system."""

from __future__ import annotations

import json

import pytest

import tstack.plugins as plugin_module
from tstack.scanner import scan_project


def _write_rule(root, payload) -> None:
    rules = root / ".tstack" / "rules"
    rules.mkdir(parents=True)
    (rules / "policy.json").write_text(json.dumps(payload), encoding="utf-8")


def test_declarative_rule_adds_namespaced_finding(tmp_path) -> None:
    (tmp_path / "legacy").mkdir()
    (tmp_path / "legacy" / "unsafe.py").write_text("print('legacy')\n", encoding="utf-8")
    _write_rule(tmp_path, {"rules": [{"id": "TTRL_LEGACY", "severity": "high", "title": "Legacy code requires migration", "path_regex": "^legacy/", "remediation": "Move the module behind a maintained interface."}]})
    report = scan_project(tmp_path)
    finding = next(item for item in report.findings if item.rule_id == "TTRL_LEGACY")
    assert finding.path == "legacy/unsafe.py"
    assert finding.plugin == "project-rules"
    assert report.plugins[0].name == "project-rules"
    assert len(report.plugins[0].integrity) == 64


def test_rule_integrity_is_deterministic(tmp_path) -> None:
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    _write_rule(tmp_path, {"rules": [{"id": "TTRL_APP", "severity": "low", "title": "App file", "path_regex": "app\\.py$"}]})
    assert scan_project(tmp_path).plugins[0].integrity == scan_project(tmp_path).plugins[0].integrity


def test_invalid_rule_fails_closed(tmp_path) -> None:
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    _write_rule(tmp_path, {"rules": [{"id": "bad id", "severity": "extreme", "path_regex": ".*"}]})
    with pytest.raises(ValueError, match="invalid declarative rule"):
        scan_project(tmp_path)


def test_custom_rule_does_not_expose_file_content(tmp_path) -> None:
    secret = "do-not-print-this-value"
    (tmp_path / "private.txt").write_text(secret, encoding="utf-8")
    _write_rule(tmp_path, {"rules": [{"id": "TTRL_PRIVATE", "severity": "medium", "title": "Private file", "path_regex": "private\\.txt$"}]})
    payload = json.dumps(scan_project(tmp_path), default=lambda value: value.__dict__)
    assert secret not in payload


def test_untrusted_plugin_is_blocked_before_load(tmp_path, monkeypatch) -> None:
    trust = tmp_path / ".tstack" / "plugin-trust.json"
    trust.parent.mkdir(parents=True)
    trust.write_text(json.dumps({"mode": "allowlist", "allowed": []}), encoding="utf-8")
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    state = {"loaded": False}

    class Dist:
        version = "1.0.0"

    class Entry:
        name = "untrusted"
        value = "untrusted_package:Rules"
        dist = Dist()
        def load(self):
            state["loaded"] = True
            raise AssertionError("plugin code must not load")

    class Entries:
        def select(self, **kwargs):
            return [Entry()]

    monkeypatch.setattr(plugin_module, "entry_points", lambda: Entries())
    with pytest.raises(ValueError, match="untrusted plugin blocked before load"):
        scan_project(tmp_path)
    assert state["loaded"] is False
